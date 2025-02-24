import { render, screen, fireEvent } from '@testing-library/react';
import axios from 'axios';
import { NotionIntegration } from './notion';

jest.mock('axios');

const mockUserNotion = 'testUser';
const mockOrgNotion = 'testOrg';
const mockCredentialsNotion = { access_token: 'mock_access_token_notion' };

describe('NotionIntegration Component', () => {
    test('renders connect button', () => {
        render(<NotionIntegration user={mockUserNotion} org={mockOrgNotion} integrationParams={{}} setIntegrationParams={jest.fn()} />);
        expect(screen.getByText('Connect to Notion')).toBeInTheDocument();
    });

    test('successful OAuth flow', async () => {
        axios.post.mockResolvedValueOnce({ data: 'http://auth-url.com' });
        axios.post.mockResolvedValueOnce({ data: mockCredentialsNotion });

        render(<NotionIntegration user={mockUserNotion} org={mockOrgNotion} integrationParams={{}} setIntegrationParams={jest.fn()} />);
        fireEvent.click(screen.getByText('Connect to Notion'));

        expect(axios.post).toHaveBeenCalledWith(expect.stringContaining('/authorize'), expect.any(FormData));
    });

    test('error during OAuth flow', async () => {
        axios.post.mockRejectedValueOnce({ response: { data: { detail: 'OAuth Error Notion' } } });

        render(<NotionIntegration user={mockUserNotion} org={mockOrgNotion} integrationParams={{}} setIntegrationParams={jest.fn()} />);
        fireEvent.click(screen.getByText('Connect to Notion'));

        expect(await screen.findByText('OAuth Error Notion')).toBeInTheDocument();
    });
});
