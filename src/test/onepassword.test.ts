import './setup.js';
import { test, describe } from 'node:test';
import assert from 'node:assert';
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
    assert.ok(credentials.username);
    assert.ok(credentials.password);
    assert.ok(typeof credentials.username === 'string');
    assert.ok(typeof credentials.password === 'string');
  });

  test('should throw error for invalid reference', async () => {
    await assert.rejects(
      () => getCredentialsFrom1Password('op://Invalid/Item/field', 'op://Invalid/Item/field'),
      /Failed to retrieve credentials/
    );
  });
});
