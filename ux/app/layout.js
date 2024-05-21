
import * as React from 'react';
import Link from 'next/link';
import { AppBar } from '@mui/material';
import { Box } from '@mui/material';
import { Drawer } from '@mui/material';
import { Toolbar } from '@mui/material';
import { Typography } from '@mui/material';
import { Divider } from '@mui/material';
import { List } from '@mui/material';
import { ListItem } from '@mui/material';
import { ListItemButton } from '@mui/material';
import { ListItemText } from '@mui/material';

import { HomeIcon } from '@mui/icons-material';
import { ChecklistIcon } from '@mui/icons-material';
import { SettingsIcon } from '@mui/icons-material';
import { PiChartLineBold } from "react-icons/pi";
import { IconButton } from '@mui/material';

import ThemeRegistry from '@/components/theme/ThemeRegistry';
import { LoginButton, LogoutButton } from '@/components/LoginButton';
import WelcomeName from '@/components/WelcomeName';

export const metadata = {
  title: 'LifeTimeLines',
  description: 'The LifeTimeLines app',
};
const DRAWER_WIDTH = 240;

const LINKS = [
  { text: 'Home', href: '/', icon: HomeIcon },
  { text: 'Entities', href: '/entities', icon: ChecklistIcon },
  { text: 'Albums', href: '/photo-albums', icon: ChecklistIcon },
];

const PLACEHOLDER_LINKS = [
  { text: 'Settings', icon: SettingsIcon },
];

function Page() {
  return <Typography>hello world</Typography>;
}
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
          <ThemeRegistry options={{ key: "mui" }}>        
            <AppBar position="fixed" sx={{ zIndex: 2000 }}>
                <Toolbar sx={{ backgroundColor: 'background.paper' }}>
                  <IconButton edge="start" color="black" aria-label="menu" href='/'>
                  <PiChartLineBold />
                  </IconButton>
                hello                  
                  <Typography variant="h6" noWrap component="div" color="black">
                    LifeTimeLines
                  </Typography>
                  <Typography variant="h10" noWrap component="div" color="black" paddingLeft={5}>
                    hello 
                    <WelcomeName/>
                  </Typography>
                </Toolbar>
              </AppBar>
              <Drawer 
                sx={{
                  width: DRAWER_WIDTH,
                  flexShrink: 0,
                  '& .MuiDrawer-paper': {
                    width: DRAWER_WIDTH,
                    boxSizing: 'border-box',
                    top: ['48px', '56px', '64px'],
                    height: 'auto',
                    bottom: 0,
                  },
                }}
                variant="permanent"
                anchor="left"
              >
                <Divider />
                <List>
                  {LINKS.map(({ text, href, icon: Icon }) => (
                    <ListItem key={href} disablePadding>
                      <ListItemButton component={Link} href={href}>
                        <ListItemText primary={text} />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
                <Divider sx={{ mt: 'auto' }} />
                <List>
                  {PLACEHOLDER_LINKS.map(({ text, icon: Icon }) => (
                    <ListItem key={text} disablePadding>
                    <ListItemButton>
                      <ListItemText primary={text} />
                    </ListItemButton>
                  </ListItem>
                ))}
                  <ListItem key="login" disablePadding>
                    <LoginButton/>
                  </ListItem>
                  <ListItem key="Logout" disablePadding>
                    <LogoutButton/>
                  </ListItem>                  
                </List>
              </Drawer>
              <Box
                component="main"
                sx={{
                  flexGrow: 1,
                  bgcolor: 'background.default',
                  ml: `${DRAWER_WIDTH}px`,
                  mt: ['48px', '56px', '64px'],
                  p: 3,
                }}
              >
                {children}
            </Box>
          </ThemeRegistry>
        </body>
    </html>
  );
};
