'use client';

import { useEffect, useState } from "react";
import { useIsAuthenticated, useMsal } from '@azure/msal-react';
import { callMsGraph } from "./graph";
import { loginRequest } from "./authConfig";

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

    // useEffect(() => {
    //     console.log("in useeffect() for loggedInName component");
    //     const { inProgress } = useMsal();

    //     setGraphData("no one logged in");

    //     async function  RequestProfileData() 
    //     {
    //         if (inProgress !== InteractionStatus.Startup && inProgress !== InteractionStatus.HandleRedirect)
    //         {
    //             // Silently acquires an access token which is then attached to a request for MS Graph data
    //             await instance
    //                     .acquireTokenSilent({
    //                         ...loginRequest,
    //                         account: accounts[0],
    //                     })
    //                     .then((response) => {
    //                         callMsGraph(response.accessToken).then((response) => setGraphData(response));
    //                         console.log(response)
    //                     });
    //         }
    //     }
    //     RequestProfileData();

    // }, [isAuthenticated, accounts, instance]);

    // return (
    //     <div>
    //         {graphData}
    //     </div>
    // )

    if (name) {
        return name;
    } else {
        return null;
    }
}


// import { useEffect, useState } from "react";
// import { useMsal } from "@azure/msal-react";
// import Typography from "@mui/material/Typography";

// const WelcomeName = () => {
//     const { instance } = useMsal();
//     const [name, setName] = useState(null);

//     const activeAccount = instance.getActiveAccount();
//     useEffect(() => {
//         if (activeAccount && activeAccount.name) {
//             setName(activeAccount.name.split(' ')[0]);
//         } else {
//             setName(null);
//         }
//     }, [activeAccount]);

//     if (name) {
//         return <Typography variant="h6">Welcome, {name}</Typography>;
//     } else {
//         return null;
//     }
// };

// export default WelcomeName;
