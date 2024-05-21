import { createClient } from "redis";
import "server-only";
import { redisUrl, redisPw, redisUser } from "@/serverConfig";

export const redisClient = createClient(
  // redisUrl ? { url: redisUrl } : undefined
  redisUrl
    ? {
        url: redisUrl,
        username: redisUser,
        password: redisPw,
      }
    : undefined
);

redisClient.on("error", (err) => console.log("Redis Client Error", err));
