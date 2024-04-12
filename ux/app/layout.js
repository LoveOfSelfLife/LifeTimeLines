// 'use client';
import * as React from 'react';
import Link from 'next/link';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import DashboardIcon from '@mui/icons-material/Dashboard';
import HomeIcon from '@mui/icons-material/Home';
import StarIcon from '@mui/icons-material/Star';
import ChecklistIcon from '@mui/icons-material/Checklist';
import SettingsIcon from '@mui/icons-material/Settings';
import { PiChartLineBold } from "react-icons/pi";
import { IconButton } from '@mui/material';
// import ThemeRegistry from '@/components/ThemeRegistry/ThemeRegistry';

import { AuthProvider } from '../components/auth/auth';
import { LogInOutButton } from '@/components/auth/LogInOutButton';
import { LoggedInName } from '@/components/auth/LoggedInName';
import { Menu } from '@mui/icons-material';

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

export default function RootLayout({ children }) {
  // const [open, setOpen] = React.useState(false);

  // const toggleDrawer = (newOpen) => () => {
  //   setOpen(newOpen);
  // };

  return (
    <html lang="en">
      <head>
        <link rel="stylesheet" href='https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700&display=swap'/>
      </head>

        <AuthProvider>
          <body>
            {/* <ThemeRegistry> */}
              <AppBar position="fixed" sx={{ zIndex: 2000 }}>
                <Toolbar sx={{ backgroundColor: 'background.paper' }}>
                  <IconButton edge="start" color="black" aria-label="menu" href='/'>
                  <PiChartLineBold />
                  </IconButton>
                  
                  {/* <DashboardIcon sx={{ color: '#444', mr: 2, transform: 'translateY(-2px)' }} /> */}
                  <Typography variant="h6" noWrap component="div" color="black">
                    LifeTimeLines
                  </Typography>
                  <Typography variant="h10" noWrap component="div" color="black" paddingLeft={5}>
                    <LoggedInName/>
                  </Typography>
                </Toolbar>
              </AppBar>
              {/* <Button onClick={toggleDrawer(true)}>Open drawer</Button> */}
              <Drawer 
                // open={open} onClose={toggleDrawer(false)}
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
                        <ListItemIcon>
                          <Icon />
                        </ListItemIcon>
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
                      <ListItemIcon>
                        <Icon />
                      </ListItemIcon>
                      <ListItemText primary={text} />
                    </ListItemButton>
                  </ListItem>
                ))}
                  <ListItem key="loginLogout" disablePadding>
                    <LogInOutButton/>
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
            {/* </ThemeRegistry> */}
          </body>
        </AuthProvider>

    </html>
  );
}
