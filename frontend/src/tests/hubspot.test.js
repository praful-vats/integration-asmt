import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import axios from 'axios';
import HubSpotIntegration from './hubspot';

jest.mock('axios');

describe('HubSpotIntegration Component', () => {
    const mockProps = {
        userId: 'TestUser',
        orgId: 'TestOrg',
        setStatusMessage: jest.fn(),
        setIntegrationParams: jest.fn(),
    };

    afterEach(() => {
        jest.clearAllMocks();
    });

    // 1. Render Component
    it('renders HubSpot integration component correctly', () => {
        render(<HubSpotIntegration {...mockProps} />);
        expect(screen.getByText('Connect HubSpot')).toBeInTheDocument();
    });

    // 2. Handle OAuth Connection Button Click
    it('handles OAuth connection button click', async () => {
        axios.post.mockResolvedValueOnce({ data: 'https://app.hubspot.com/oauth/authorize?mock' });

        render(<HubSpotIntegration {...mockProps} />);
        const connectButton = screen.getByText('Connect HubSpot');
        fireEvent.click(connectButton);

        expect(axios.post).toHaveBeenCalledWith('/integrations/hubspot/authorize', {
            user_id: 'TestUser',
            org_id: 'TestOrg',
        });
        expect(global.window.location.href).toBe('https://app.hubspot.com/oauth/authorize?mock');
    });

    // 3. Handle Status Message Display
    it('displays status message when connected', () => {
        render(<HubSpotIntegration {...mockProps} />);
        const statusMessage = screen.getByTestId('status-message');
        fireEvent.change(statusMessage, { target: { value: 'Connected to HubSpot' } });

        expect(statusMessage.value).toBe('Connected to HubSpot');
    });

    // 4. Fetch Credentials
    it('fetches credentials and updates integration parameters', async () => {
        axios.post.mockResolvedValueOnce({ data: { access_token: 'mock_token' } });

        render(<HubSpotIntegration {...mockProps} />);
        const fetchButton = screen.getByText('Fetch Credentials');
        fireEvent.click(fetchButton);

        expect(axios.post).toHaveBeenCalledWith('/integrations/hubspot/credentials', {
            user_id: 'TestUser',
            org_id: 'TestOrg',
        });

        // Wait for async state update
        await screen.findByText('Credentials fetched successfully');
        expect(mockProps.setIntegrationParams).toHaveBeenCalledWith({
            credentials: '{"access_token":"mock_token"}',
        });
    });

    // 5. Handle Errors
    it('handles errors and displays message', async () => {
        axios.post.mockRejectedValueOnce({ response: { data: { detail: 'Error fetching credentials' } } });

        render(<HubSpotIntegration {...mockProps} />);
        const fetchButton = screen.getByText('Fetch Credentials');
        fireEvent.click(fetchButton);

        await screen.findByText('Error fetching credentials');
        expect(mockProps.setStatusMessage).toHaveBeenCalledWith('Error fetching credentials');
    });
});
