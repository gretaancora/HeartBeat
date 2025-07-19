// index.mjs

import { CognitoIdentityProviderClient, InitiateAuthCommand } from "@aws-sdk/client-cognito-identity-provider";
import crypto from "crypto";

// Configura la regione (assicurati sia quella giusta)
const REGION = "us-east-1";

// Istanzia il client Cognito v3
const client = new CognitoIdentityProviderClient({ region: REGION });

// Sostituisci questi valori con i tuoi
const USER_POOL_ID = "us-east-1_MMIaRW7by";
const CLIENT_ID      = "7behact4mbieppe861t2lc869h";
const CLIENT_SECRET  = "371943ja3iknc6pqsj5g77ujj3udae2cngpjqo6jus2vn8qhsrr";

// Crea hash per autenticazione con client segreto
function generateSecretHash(username) {
  return crypto
    .createHmac("SHA256", CLIENT_SECRET)
    .update(username + CLIENT_ID)
    .digest("base64");
}

// Headers per supporto CORS
const CORS_HEADERS = {
  "Access-Control-Allow-Origin":  "*",
  "Access-Control-Allow-Methods": "POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,Authorization"
};

export const handler = async (event, context) => {
  context.callbackWaitsForEmptyEventLoop = false;

  console.log("[DEBUG] Evento ricevuto:", JSON.stringify(event));

  // Gestione preflight (CORS)
  if (event.httpMethod === "OPTIONS") {
    return {
      statusCode: 200,
      headers:    CORS_HEADERS,
      body:       ""
    };
  }

  // Consenti solo POST
  if (event.httpMethod !== "POST") {
    return {
      statusCode: 405,
      headers:    CORS_HEADERS,
      body:       JSON.stringify({ error: "Method Not Allowed" })
    };
  }

  // Parsing sicuro JSON
  let body;
  try {
    body = typeof event.body === "string"
      ? JSON.parse(event.body)
      : event.body;
  } catch (err) {
    console.error("[ERROR] Parsing JSON fallito:", err);
    return {
      statusCode: 400,
      headers:    CORS_HEADERS,
      body:       JSON.stringify({ error: "Invalid JSON body" })
    };
  }

  const { email, password } = body;
  if (!email || !password) {
    return {
      statusCode: 400,
      headers:    CORS_HEADERS,
      body:       JSON.stringify({ error: "Email e password richieste" })
    };
  }

  // Prepara i parametri per initiateAuth
  const params = {
    AuthFlow:       "USER_PASSWORD_AUTH",
    ClientId:       CLIENT_ID,
    AuthParameters: {
      USERNAME:    email,
      PASSWORD:    password,
      SECRET_HASH: generateSecretHash(email)
    }
  };

  try {
    console.log("[DEBUG] Inizio autenticazione con Cognito:", email);
    const command = new InitiateAuthCommand(params);
    const result  = await client.send(command);
    console.log("[DEBUG] Autenticazione riuscita:", result);

    const { IdToken, AccessToken } = result.AuthenticationResult;

    return {
      statusCode: 200,
      headers:    CORS_HEADERS,
      body:       JSON.stringify({ idToken: IdToken, accessToken: AccessToken })
    };
  } catch (err) {
    console.error("[ERROR] Cognito login fallito:", err);
    return {
      statusCode: err.$metadata?.httpStatusCode || 500,
      headers:    CORS_HEADERS,
      body:       JSON.stringify({ error: err.message || "Errore interno" })
    };
  }
};
