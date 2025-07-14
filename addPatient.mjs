import { CognitoIdentityProviderClient, SignUpCommand, AdminConfirmSignUpCommand, AdminAddUserToGroupCommand } from "@aws-sdk/client-cognito-identity-provider";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";
import crypto from "crypto";

// Environment variables
const USER_POOL_ID = process.env.USER_POOL_ID;
const APP_CLIENT_ID = process.env.APP_CLIENT_ID;
const APP_CLIENT_SECRET = process.env.APP_CLIENT_SECRET;
const PATIENT_GROUP = process.env.PATIENT_GROUP;
const DDB_TABLE_NAME = process.env.DDB_TABLE_NAME;

// Validate required environment variables
if (!USER_POOL_ID || !APP_CLIENT_ID || !APP_CLIENT_SECRET || !PATIENT_GROUP || !DDB_TABLE_NAME) {
  throw new Error(
    "Missing required env vars: USER_POOL_ID, APP_CLIENT_ID, APP_CLIENT_SECRET, PATIENT_GROUP, DDB_TABLE_NAME"
  );
}

// Initialize AWS SDK clients
const cognitoClient = new CognitoIdentityProviderClient({});
const ddbClient = new DynamoDBClient({});
const ddbDocClient = DynamoDBDocumentClient.from(ddbClient);

/**
 * Compute the secret hash for Cognito calls on a client with a secret.
 */
function getSecretHash(username) {
  const hmac = crypto.createHmac('sha256', APP_CLIENT_SECRET);
  hmac.update(username + APP_CLIENT_ID);
  return hmac.digest('base64');
}

/**
 * Parse a JWT token payload without dependencies (ES module)
 */
function parseJwt(token) {
  const parts = token.split('.');
  if (parts.length !== 3) throw new Error('Invalid JWT format');
  const payload = parts[1];
  const decoded = Buffer.from(payload, 'base64').toString('utf8');
  return JSON.parse(decoded);
}

/**
 * Lambda handler for user signup and doctor-patient linking
 */
export const handler = async (event) => {
  console.info('Event:', JSON.stringify(event));

  // Parse body
  let body;
  try {
    body = JSON.parse(event.body || '{}');
  } catch {
    return { statusCode: 400, body: JSON.stringify({ message: 'Invalid JSON' }) };
  }

  const { email, password } = body;
  if (!email || !password) {
    return { statusCode: 400, body: JSON.stringify({ message: 'Email and password required' }) };
  }

  try {
    // 1) Sign up
    const secretHash = getSecretHash(email);
    await cognitoClient.send(
      new SignUpCommand({
        ClientId: APP_CLIENT_ID,
        Username: email,
        Password: password,
        SecretHash: secretHash,
        UserAttributes: [{ Name: 'email', Value: email }],
      })
    );

    // 2) Confirm
    await cognitoClient.send(
      new AdminConfirmSignUpCommand({ UserPoolId: USER_POOL_ID, Username: email })
    );

    // 3) Add to group
    await cognitoClient.send(
      new AdminAddUserToGroupCommand({ UserPoolId: USER_POOL_ID, Username: email, GroupName: PATIENT_GROUP })
    );

        // 4) Extract doctor (use email if available)
    let doctor;
    const claims = event.requestContext?.authorizer?.claims;
    if (claims) {
      // Prefer email claim
      doctor = claims.email || claims['email'] || claims['cognito:username'] || claims.username;
    }
    // Fallback: parse JWT from header
    if (!doctor) {
      const auth = event.headers?.authorization || event.headers?.Authorization;
      if (auth && auth.startsWith('Bearer ')) {
        try {
          const token = auth.slice(7);
          const payload = parseJwt(token);
          doctor = payload.email || payload['email'] || payload['cognito:username'] || payload.username;
          console.info(`Doctor extracted from JWT payload: ${doctor}`);
        } catch (e) {
          console.warn('JWT parse failed for doctor extraction', e);
        }
      }
    }
    if (!doctor) {
      console.warn('Doctor still not found; defaulting to UNKNOWN_DOCTOR');
      doctor = 'UNKNOWN_DOCTOR';
    }

    // 5) Persist
    await ddbDocClient.send(
      new PutCommand({ TableName: DDB_TABLE_NAME, Item: { doctor, patient: email } })
    );

    return {
      statusCode: 200,
      body: JSON.stringify({
        message: `User ${email} registered, confirmed, added to group ${PATIENT_GROUP}, linked to doctor ${doctor}`,
      }),
    };
  } catch (err) {
    console.error('Flow error', err);
    return { statusCode: 500, body: JSON.stringify({ message: err.message }) };
  }
};
