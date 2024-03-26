'use client';

import LogoutIcon from '@mui/icons-material/Logout';
import LoginIcon from  '@mui/icons-material/Login';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import { useIsAuthenticated, useMsal } from '@azure/msal-react';
import { loginRequest } from "./authConfig";

export function LogInOutButton()
{
    const { instance } = useMsal();
    const handleLogin = () => {
        console.log("in handleLogin");
        instance.loginPopup(loginRequest).catch(e => {
            console.log('exception during login: ' + e);
        });
    }
    
    const handleLogout = () => {
        console.log("in handleLogout");
        instance.logoutPopup({
            postLogoutRedirectUri: "/",
            mainWindowRedirectUri: "/"
        });
    }

    const isAuthenticated = useIsAuthenticated();
    if (!isAuthenticated) 
    {
        return (
        <ListItemButton onClick={() => handleLogin()}>
            <ListItemIcon>
            <LoginIcon />
            </ListItemIcon>
            <ListItemText primary="Login" />
        </ListItemButton>
        )
        }
    else
    {
        return (
        <ListItemButton onClick={() => handleLogout()}>
            <ListItemIcon>
            <LogoutIcon />
            </ListItemIcon>
            <ListItemText primary="Logout" />
        </ListItemButton>
        )
    }
}