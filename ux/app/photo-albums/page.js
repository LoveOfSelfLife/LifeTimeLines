'use client'

import * as React from 'react';
import { Container } from '@mui/material';
import { Box } from '@mui/material';

import { useState, useEffect } from 'react';
import { useIsAuthenticated, useMsal, AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import { fetch_wrapper } from '@/actions/service_fetch_wrapper';

// import the react-json-view component
// import { ReactJson } from '@microlink/react-json-view'
// const Fuse = (await import('fuse.js')).default
// const ReactJson = (await import('@microlink/react-json-view')).default

export default function JsonPage() {

  const [apiData, setApiData] = useState( null );
  const msalContext = useMsal();
  const isAuthenticated_2 = useIsAuthenticated();

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    fetch_wrapper('photos', 'photos/albums', 'GET', null, apiData, setApiData, msalContext, { isAuthenticated_2 });
  }, [msalContext.instance, msalContext.accounts, msalContext.inProgress, apiData, msalContext, isAuthenticated_2]);
  try {
    return (
      apiData === null ?
      <div>Loading...</div>
      :
      <div>
        <Container>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
            }}>
            <AuthenticatedTemplate>
              <p>Signed in as: {msalContext.accounts[0]?.username}</p>
              {/* <ReactJson src={apiData?apiData:[]} /> */}
            </AuthenticatedTemplate>
            <UnauthenticatedTemplate>
              <p>No one is signed in!</p>
            </UnauthenticatedTemplate>
          </Box>
        </Container>
      </div>
    );
  } catch (error) {
    console.log('Error in JsonPage: ', error);
    return (
      <div>
        <p>There was an error loading the data.</p>
      </div>
    );  
  }
};


