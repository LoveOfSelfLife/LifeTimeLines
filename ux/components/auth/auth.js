'use client'

import { PublicClientApplication } from '@azure/msal-browser';
import { MsalProvider } from '@azure/msal-react';
import { msalConfig } from './authConfig';

const msalInstance = new PublicClientApplication(msalConfig);

export function AuthProvider({children})
{
    console.log("in Auth");
    return (
        <MsalProvider instance={msalInstance}>
            {children}
        </MsalProvider>
    )
}
