import { execSync } from 'child_process';

export interface OnePasswordConfig {
  item: string;
  vault?: string;
  account?: string;
}

/**
 * Retrieve credentials from 1Password using secret references
 * @param usernameRef - 1Password secret reference (e.g., "op://Your-Vault/Your-Item/username")
 * @param passwordRef - 1Password secret reference (e.g., "op://Your-Vault/Your-Item/password")
 */
export async function getCredentialsFrom1Password(
  usernameRef: string,
  passwordRef: string
): Promise<{ username: string; password: string }> {
  try {
    const username = execSync(`op read "${usernameRef}"`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();

    const password = execSync(`op read "${passwordRef}"`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();

    return { username, password };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to retrieve credentials from 1Password: ${errorMessage}. Make sure you're signed in to 1Password and the references are correct.`);
  }
}
