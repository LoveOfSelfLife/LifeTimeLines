'use client'

import { useDispatch, useSelector } from "react-redux";
import { useMsal, AuthenticatedTemplate, UnauthenticatedTemplate } from "@azure/msal-react";
import { setUser } from "@/features/auth/authSlice";

export function User()
{
    const dispatch = useDispatch('auth');
    var user = "no one is logged in";
    const { instance, accounts } = useMsal();
    // const user = useSelector((state) => state.auth.user); 
    console.log('in user')
    if (accounts && accounts.length > 0) {
        console.log("someone is logged in");
        console.log(accounts[0]);
        dispatch(setUser(accounts[0].username))
        user = accounts[0].username;
    };

    return (
        <div>
            <AuthenticatedTemplate>
                <div>{user} is logged in</div>
            </AuthenticatedTemplate>

            <UnauthenticatedTemplate>
                logged-out
            </UnauthenticatedTemplate>
            </div>
    )
}


