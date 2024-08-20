import { SessionPartitionManager } from "../utils/SessionPartitionManager";
import RedisCacheClient from "../utils/RedisCacheClient";
import { redisClient } from "./redis";
import { AuthProvider } from "@/utils/AuthProvider";
import { getSession } from "./session";
import { cookies } from "next/headers";
import { authCallbackUri, msalConfig } from "@/serverConfig";
import "server-only";

async function partitionManagerFactory() {
  const cookie = cookies().get("__session");

  const session = await getSession(`__session=${cookie?.value}`);

  return new SessionPartitionManager(session);
}

export const authProvider = new AuthProvider(
  msalConfig,
  authCallbackUri!,
  new RedisCacheClient(redisClient),
  partitionManagerFactory
);

export async function authenticated_fetch(url: string) {
  const { account, instance } = await authProvider.authenticate();

  if (!account) {
    return null;
  }

  const token = await instance.acquireTokenSilent({
    account,
    scopes: [ process.env.APP_SCOPE! ],
  });

  if (!token) {
    return null;
  }

  const response = await fetch(url, {
    headers: {
      'Content-Type' : 'application/json',       
      'Authorization': 'Bearer ' +   token.accessToken,
    }
  });
  return response;
}