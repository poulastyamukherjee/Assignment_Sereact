"""
Test cases for WebSocket functionality in app_websocket.py
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import websockets

# Import the websocket module
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import app_websocket
except ImportError:
    # Handle case where app_websocket doesn't exist yet
    app_websocket = None


@pytest.mark.asyncio
class TestWebSocketFunctions:
    """Test WebSocket related functions."""

    @pytest.mark.skipif(app_websocket is None, reason="app_websocket module not available")
    async def test_send_to_all_with_clients(self):
        """Test sending data to all connected clients."""
        # Mock connected clients
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        
        app_websocket.connected_clients = {mock_client1, mock_client2}
        
        test_data = "test message"
        
        await app_websocket.send_to_all(test_data)
        
        # Verify both clients received the message
        mock_client1.send.assert_called_once_with(test_data)
        mock_client2.send.assert_called_once_with(test_data)

    @pytest.mark.skipif(app_websocket is None, reason="app_websocket module not available")
    async def test_send_to_all_no_clients(self):
        """Test sending data when no clients are connected."""
        app_websocket.connected_clients = set()
        
        test_data = "test message"
        
        # Should not raise an error
        await app_websocket.send_to_all(test_data)

    @pytest.mark.skipif(app_websocket is None, reason="app_websocket module not available")
    def test_has_connected_clients_true(self):
        """Test has_connected_clients when clients are connected."""
        mock_client = Mock()
        app_websocket.connected_clients = {mock_client}
        
        assert app_websocket.has_connected_clients() is True

    @pytest.mark.skipif(app_websocket is None, reason="app_websocket module not available")
    def test_has_connected_clients_false(self):
        """Test has_connected_clients when no clients are connected."""
        app_websocket.connected_clients = set()
        
        assert app_websocket.has_connected_clients() is False

class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality with the main app."""

    def test_websocket_integration_with_app(self):
        """Test that the main app can communicate with WebSocket module."""
        if app_websocket is None:
            pytest.skip("app_websocket module not available")
        
        # Import the main app
        import app
        
        # Test has_connected_clients function
        with patch.object(app_websocket, 'connected_clients', set()):
            assert app.has_connected_clients() is False
        
        # Test with mock client
        mock_client = Mock()
        with patch.object(app_websocket, 'connected_clients', {mock_client}):
            assert app.has_connected_clients() is True

    @pytest.mark.asyncio
    async def test_send_to_websocket_integration(self):
        """Test the send_to_websocket function integration."""
        if app_websocket is None:
            pytest.skip("app_websocket module not available")
        
        import app
        
        test_data = {"test": "data"}
        
        with patch('app.has_connected_clients', return_value=True), \
             patch('app.send_to_all') as mock_send_all, \
             patch('asyncio.new_event_loop') as mock_new_loop, \
             patch('asyncio.set_event_loop') as mock_set_loop:
            
            mock_loop = Mock()
            mock_new_loop.return_value = mock_loop
            
            app.send_to_websocket(test_data)
            
            # Verify the event loop handling
            mock_new_loop.assert_called_once()
            mock_set_loop.assert_called_once_with(mock_loop)
            mock_loop.run_until_complete.assert_called_once()
            mock_loop.close.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])