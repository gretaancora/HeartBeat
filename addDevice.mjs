import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";

// Environment variable for DynamoDB table
const DDB_TABLE_NAME = process.env.DDB_TABLE_NAME;
if (!DDB_TABLE_NAME) {
  throw new Error("Missing required env var: DDB_TABLE_NAME");
}

// Initialize DynamoDB client
const ddbClient = new DynamoDBClient({});
const ddbDocClient = DynamoDBDocumentClient.from(ddbClient);

/**
 * Parse a JWT token payload without external dependencies
 */
function parseJwt(token) {
  const parts = token.split('.');
  if (parts.length !== 3) throw new Error('Invalid JWT format');
  const payload = parts[1];
  const decoded = Buffer.from(payload, 'base64').toString('utf8');
  return JSON.parse(decoded);
}

/**
 * Normalize input entries: accept single object or array of objects
 */
function normalizeEntries(body) {
  if (Array.isArray(body)) return body;
  if (body && typeof body === 'object') return [body];
  throw new Error('Request body must be an object or array of objects');
}

/**
 * Lambda handler for adding device entries linked to a patient
 */
export const handler = async (event) => {
  console.info('Received event', JSON.stringify(event));

  // Validate auth header
  const authHeader = event.headers?.authorization || event.headers?.Authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return { statusCode: 401, body: JSON.stringify({ message: 'Unauthorized' }) };
  }

  // Extract patientId from JWT
  let patientId;
  try {
    const token = authHeader.slice(7);
    const payload = parseJwt(token);
    patientId = payload['cognito:username'] || payload.username || payload.email;
    if (!patientId) throw new Error('Username claim missing');
  } catch (err) {
    console.error('Token parse error', err);
    return { statusCode: 400, body: JSON.stringify({ message: 'Invalid token' }) };
  }

  // Parse and normalize body entries
  let entries;
  try {
    const parsed = JSON.parse(event.body || '{}');
    entries = normalizeEntries(parsed);
  } catch (err) {
    console.error('Body parse error', err);
    return { statusCode: 400, body: JSON.stringify({ message: 'Invalid JSON body or format' }) };
  }

  // Process each entry
  const results = [];
  for (const entry of entries) {
    const { deviceId, age, sex } = entry;
    if (!deviceId || age === undefined || !sex) {
      results.push({ entry, status: 'failed', reason: 'deviceId, age, and sex required' });
      continue;
    }

    const item = { patientId, deviceId, age, sex };
    try {
      await ddbDocClient.send(
        new PutCommand({ TableName: DDB_TABLE_NAME, Item: item })
      );
      results.push({ entry: item, status: 'success' });
    } catch (err) {
      console.error('DynamoDB error for', entry, err);
      results.push({ entry, status: 'failed', reason: err.message });
    }
  }

  return {
    statusCode: 200,
    body: JSON.stringify({ message: 'Processed entries', results }),
  };
};
