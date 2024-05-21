// https://nextjs.org/docs/getting-started/react-essentials#the-server-only-package
// importing server-only as this module contains secrets that should not be exposed to the client

import "server-only";
import { Configuration, LogLevel } from "@azure/msal-node";

export const msalConfig: Configuration = {
  auth: {
    clientId: process.env.AZURE_AD_CLIENT_ID!,
    clientSecret: process.env.AZURE_AD_CLIENT_SECRET!,
    authority: process.env.AZURE_AD_AUTHORITY!,
  },
  system: {
    loggerOptions: {
      piiLoggingEnabled: false,
      logLevel: LogLevel.Info,
      loggerCallback(logLevel, message) {
        switch (logLevel) {
          case LogLevel.Error:
            console.error(message);
            return;
          case LogLevel.Info:
            console.info(message);
            return;
          case LogLevel.Verbose:
            console.debug(message);
            return;
          case LogLevel.Warning:
            console.warn(message);
            return;
          default:
            console.log(message);
            return;
        }
      },
    },
  },
};

export const loginRequest = { scopes: [ process.env.APP_SCOPE! ] };

export const authCallbackUri = process.env.AZURE_AD_CALLBACK_URI;
export const sessionSecret = process.env.SESSION_SECRET!;

export const redisUrl = process.env.REDIS_URL;
export const redisUser = process.env.REDIS_USER;
export const redisPw = process.env.REDIS_PASSWORD;
