'use client'

import * as React from 'react';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { useState, useEffect } from 'react';
import { useIsAuthenticated, useMsal, AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import { fetch_wrapper } from '@/actions/service_fetch_wrapper';
// import the react-json-view component
import ReactJson from '@microlink/react-json-view'


export default function JsonPage() {
  // const [apiData, setApiData] = useState( [ "loading..." ] );
  const [apiData, setApiData] = useState( null );
  const msalContext = useMsal();
  const isAuthenticated_2 = useIsAuthenticated();

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    fetch_wrapper('photos', 'photos/albums', 'GET', null, apiData, setApiData, msalContext, { isAuthenticated_2 });
  }, [msalContext.instance, msalContext.accounts, msalContext.inProgress, apiData, msalContext]);

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

            {/* <Typography variant="body1" gutterBottom>
              Json Page
            </Typography> */}
            <p>Signed in as: {msalContext.accounts[0]?.username}</p>

            <ReactJson src={apiData?apiData:[]} />

          </AuthenticatedTemplate>
          <UnauthenticatedTemplate>
            <p>No one is signed in!</p>
          </UnauthenticatedTemplate>
        </Box>
      </Container>

    </div>
  );
}


