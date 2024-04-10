'use client';

import { useEffect, useState } from "react";
import { useIsAuthenticated, useMsal } from '@azure/msal-react';

export function LoggedInName()
{
    console.log("in loggedInName() component");

    const { instance, accounts } = useMsal();
    const isAuthenticated = useIsAuthenticated();
    const [graphData, setGraphData] = useState("no one logged in");

    // const { instance } = useMsal();
    const [name, setName] = useState(null);

    const activeAccount = instance.getActiveAccount();
    useEffect(() => {
        // if (activeAccount)
        if (isAuthenticated)
        {
            // console.log(activeAccount);

            // if (activeAccount.name) {
            if (accounts.length > 0)
            {
                setName(accounts[0].name)
                return;
            } 
        }
        setName(null);
    }, [isAuthenticated, accounts]);
    if (name) {
        return name;
    } else {
        return null;
    }
}
