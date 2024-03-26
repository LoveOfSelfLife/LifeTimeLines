'use client'

import React from "react";
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "./authConfig";
import DropdownButton from "react-bootstrap/DropdownButton";
import Dropdown from "react-bootstrap/Dropdown";

/**
 * Renders a drop down button with child buttons for logging in with a popup or redirect
 */
export function SignInButton() {
    const { instance } = useMsal();

    const handleLogin = () => {
        console.log("in handleLogin");
        instance.loginPopup(loginRequest).catch(e => {
            console.log(e);
        });
    }
    const handleLogout = () => {
        console.log("in handleLogout");
        instance.loginPopup(loginRequest).catch(e => {
            console.log(e);
        });
    }


    return (
        <div>
        {/* <DropdownButton variant="secondary" className="ml-auto" drop="start" title="Sign In">
            <Dropdown.Item as="button" onClick={() => handleLogin("popup")}>Sign in using Popup</Dropdown.Item>
            <Dropdown.Item as="button" onClick={() => handleLogin("redirect")}>Sign in using Redirect</Dropdown.Item>
        </DropdownButton> */}
        <button onClick={() => handleLogin("popup")}>Sign in using Popup</button>
        
        </div>
    )
}
