'use client'

import { useIsAuthenticated } from '@azure/msal-react';
import { SignInButton } from '@/components/auth/signinbutton'
import { SignOutButton } from '@/components/auth/signoutbutton'

export function SignButtons() {
    const isAuthenticated = useIsAuthenticated();

    if (isAuthenticated)
        return <SignOutButton /> 
    else
        return <SignInButton />
  }
  