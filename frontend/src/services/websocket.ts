/**
 * WebSocket Service
 * Real-time updates for WATCHKEEPER
 */

import { io, Socket } from 'socket.io-client';
import type { WebSocketMessage } from '../types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

type MessageHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(token: string): void {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io(WS_URL, {
      auth: { token },
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('reconnect_attempt', () => {
      this.reconnectAttempts++;
      console.log(`WebSocket reconnection attempt ${this.reconnectAttempts}`);
    });

    this.socket.on('message', (data: WebSocketMessage) => {
      this.handleMessage(data);
    });

    // Specific event handlers
    this.socket.on('intelligence', (data) => {
      this.handleMessage({ ...data, type: 'intelligence' });
    });

    this.socket.on('alert', (data) => {
      this.handleMessage({ ...data, type: 'alert' });
    });

    this.socket.on('incident', (data) => {
      this.handleMessage({ ...data, type: 'incident' });
    });

    this.socket.on('personnel_location', (data) => {
      this.handleMessage({ ...data, type: 'personnel_location' });
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.handlers.clear();
  }

  subscribe(topic: string): void {
    if (this.socket) {
      this.socket.emit('subscribe', { topic });
    }
  }

  unsubscribe(topic: string): void {
    if (this.socket) {
      this.socket.emit('unsubscribe', { topic });
    }
  }

  on(eventType: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(eventType)?.delete(handler);
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    // Call handlers for specific message type
    const typeHandlers = this.handlers.get(message.type);
    if (typeHandlers) {
      typeHandlers.forEach((handler) => handler(message));
    }

    // Call handlers for all messages
    const allHandlers = this.handlers.get('*');
    if (allHandlers) {
      allHandlers.forEach((handler) => handler(message));
    }
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }
}

export const websocket = new WebSocketService();
export default websocket;
