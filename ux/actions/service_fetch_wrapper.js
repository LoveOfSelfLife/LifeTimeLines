'use client';
import { fetch_action } from './fetch_action';

import {
  InteractionRequiredAuthError,
  InteractionStatus
} from "@azure/msal-browser";


export function fetch_wrapper(service, path, method, payload, apiData, setApiData, msalContext, isAuthenticated) {
  (async () => {
    const { isAuthenticated_2 } = isAuthenticated;
    const { instance, inProgress, accounts } = msalContext;
    console.log('service_call: ' + service + ' ' + path);
    console.log('isAuthenticated_2: ' + isAuthenticated_2);

    if (!apiData && inProgress === InteractionStatus.None) {
      console.log('in first block');
      const accessTokenRequest = {
        scopes: [process.env.NEXT_PUBLIC_LIFETIMELINES_SCOPE],
        account: accounts[0],
      };
      try {
        console.log('trying to acquire token silently with accessTokenRequest: ' + JSON.stringify(accessTokenRequest));
        let accessTokenResponse = await instance.acquireTokenSilent(accessTokenRequest);
        const response = await fetch_action(service, path, method, payload, accessTokenResponse.accessToken);
        console.log('response: ' + response);
        setApiData(response);
      } 
      catch (error) {
        console.log('error: ' + error);
        if (error instanceof InteractionRequiredAuthError) {
          try {
            console.log('trying to acquire token popup');
            let accessTokenResponse = await instance.acquireTokenPopup(accessTokenRequest);
            // acquireTokenSilent(accessTokenRequest);
            const response = await fetch_action(service, path, method, payload, accessTokenResponse.accessToken);
            console.log('response: ' + response);
            setApiData(response);
          } 
          catch (error) {
              console.log(error);
          }
        }
      }
    }
  })();
}
