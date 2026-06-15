import { ApiError, SessionExpiredError } from '@/api/client';

import { getUserFacingError } from '../errors';

describe('getUserFacingError', () => {
  it('treats a fetch TypeError as a connection problem (retryable)', () => {
    const result = getUserFacingError(new TypeError('Network request failed'));
    expect(result.title).toBe('No connection');
    expect(result.retryable).toBe(true);
    expect(result.message).toMatch(/connection/i);
  });

  it('maps a session-expiry to a sign-in prompt (not retryable)', () => {
    const result = getUserFacingError(new SessionExpiredError());
    expect(result.title).toBe('Signed out');
    expect(result.retryable).toBe(false);
  });

  it('treats a 5xx as a retryable server error', () => {
    const result = getUserFacingError(new ApiError(503, 'Service Unavailable'));
    expect(result.retryable).toBe(true);
    expect(result.message).toMatch(/try again/i);
  });

  it('shows a 4xx validation message verbatim and does not offer retry', () => {
    const result = getUserFacingError(new ApiError(400, 'Starting XI needs at least 6 batters.'));
    expect(result.message).toBe('Starting XI needs at least 6 batters.');
    expect(result.retryable).toBe(false);
  });

  it('marks 429 / 408 as retryable', () => {
    expect(getUserFacingError(new ApiError(429, 'Too Many Requests')).retryable).toBe(true);
    expect(getUserFacingError(new ApiError(408, 'Request Timeout')).retryable).toBe(true);
  });

  it('falls back to a generic message for unknown errors', () => {
    expect(getUserFacingError(new Error('boom')).message).toBe('boom');
    expect(getUserFacingError('weird').message).toMatch(/unexpected/i);
  });
});
