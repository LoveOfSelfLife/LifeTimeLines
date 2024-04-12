'use server';

import { services_map } from './map_service';

export const fetch_action = async (service, path, method, payload, token) => {
    try {
        const url = services_map[service] + path;
        console.log('running fetch_action(' + url + ', ' + method + ', ' + token + ')');
        const options = { 
            method: method, 
            headers: { 
                'Content-Type': 'application/json', 
                'Authorization': 'Bearer ' + token } 
        };
        if (method != 'GET' && payload != null) {
            options.body = JSON.stringify(payload);
        }

        const response = await fetch(url, options);
        const data = await response.json();

        console.log('data from request: ' + data);
        return data;
    } 
    catch (error) {
        console.log(error);
    }
};
