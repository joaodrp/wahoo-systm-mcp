import './setup.js';
import { test, describe, expect } from 'vitest';
import { getCredentialsFrom1Password } from '../onepassword.js';

describe('1Password Integration', () => {
  test('should retrieve credentials from 1Password', async () => {
    const usernameRef = process.env.WAHOO_USERNAME_1P_REF;
    const passwordRef = process.env.WAHOO_PASSWORD_1P_REF;

    if (!usernameRef || !passwordRef) {
      console.log('Skipping 1Password test - no references provided');
      return;
    }

    const credentials = await getCredentialsFrom1Password(usernameRef, passwordRef);
    expect(credentials.username).toBeTruthy();
    expect(credentials.password).toBeTruthy();
    expect(typeof credentials.username).toBe('string');
    expect(typeof credentials.password).toBe('string');
  });

  test('should throw error for invalid reference', async () => {
    await expect(() => getCredentialsFrom1Password('op://Invalid/Item/field', 'op://Invalid/Item/field'))
      .rejects.toThrow(/Failed to retrieve credentials/);
  });
});
