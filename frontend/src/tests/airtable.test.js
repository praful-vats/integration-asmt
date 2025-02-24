import { render, screen, fireEvent } from '@testing-library/react';
import axios from 'axios';
import { AirtableIntegration } from './airtable';

jest.mock('axios');

const mockUser = 'testUser';
const mockOrg = 'testOrg';
const mockCredentials = { access_token: 'mock_access_token' };

describe('AirtableIntegration Component', () => {
    test('renders connect button', () => {
        render(<AirtableIntegration user={mockUser} org={mockOrg} integrationParams={{}} setIntegrationParams={jest.fn()} />);
        expect(screen.getByText('Connect to Airtable')).toBeInTheDocument();
    });

    test('successful OAuth flow', async () => {
        axios.post.mockResolvedValueOnce({ data: 'http://auth-url.com' });
        axios.post.mockResolvedValueOnce({ data: mockCredentials });

        render(<AirtableIntegration user={mockUser} org={mockOrg} integrationParams={{}} setIntegrationParams={jest.fn()} />);
        fireEvent.click(screen.getByText('Connect to Airtable'));

        expect(axios.post).toHaveBeenCalledWith(expect.stringContaining('/authorize'), expect.any(FormData));
    });

    test('error during OAuth flow', async () => {
        axios.post.mockRejectedValueOnce({ response: { data: { detail: 'OAuth Error' } } });

        render(<AirtableIntegration user={mockUser} org={mockOrg} integrationParams={{}} setIntegrationParams={jest.fn()} />);
        fireEvent.click(screen.getByText('Connect to Airtable'));

        expect(await screen.findByText('OAuth Error')).toBeInTheDocument();
    });
});