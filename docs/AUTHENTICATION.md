## Non-interactive authentication for SharePoint provisioning scripts

This folder's PowerShell scripts use Microsoft Entra (Azure AD) client credentials (application) authentication and Microsoft Graph to provision SharePoint lists without interactive signin.

Summary
- Auth method: OAuth2 client credentials grant (client id + client secret).
- Token endpoint: `https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token`.
- Scope used: `https://graph.microsoft.com/.default` (requests app permissions).
- API: Microsoft Graph (`https://graph.microsoft.com/v1.0`) to manage sites, lists, and columns.

Required application setup (in target tenant)
1. Register an application in Microsoft Entra (Azure AD).
2. Under "Certificates & secrets" create a client secret (or upload certificate).
3. Under "API permissions" add **Application** permissions (NOT Delegated):
   - `Sites.ReadWrite.All` (minimum) OR
   - `Sites.FullControl.All` (if you need full control)
4. Click **Grant admin consent** for the permissions (tenant admin required).

Required environment variables
The scripts read credentials from a `.env` file placed next to the scripts (workspace root relative). Required variables:

- `ENTRA_TENANT_ID` — the tenant (directory) id or domain.
- `ENTRA_CLIENT_ID` — the application (client) id.
- `ENTRA_CLIENT_SECRET` — the client secret value.

Example `.env` (do NOT commit secrets):

ENTRA_TENANT_ID=your-tenant-id
ENTRA_CLIENT_ID=your-client-id
ENTRA_CLIENT_SECRET="your-client-secret"

How the scripts authenticate (implementation notes)
- `Get-GraphToken` in `create-registrations-graph.ps1` posts to the token endpoint with body:
  - `client_id`, `client_secret`, `grant_type=client_credentials`, `scope=https://graph.microsoft.com/.default`.
- The returned `access_token` is used in `Authorization: Bearer {token}` headers for subsequent Graph calls.
- The scripts use Graph endpoints such as `/sites/{host}:{sitePath}:`, `/sites/{siteId}/lists`, and `/sites/{siteId}/lists/{listId}/columns`.

Key scripts and behavior
- `create-registrations-graph.ps1` — primary non-interactive provisioning script. It:
  - Loads `.env` values into process environment variables.
  - Acquires a Graph token via client credentials.
  - Resolves the SharePoint site (`/sites/{host}:{path}:` → site id).
  - Deletes an existing `Registrations` list when `-Force` is provided (polls until removed).
  - Creates the `Registrations` list and columns via Microsoft Graph.

- `decode-token.ps1` — helper to decode the JWT and inspect claims (useful to confirm the token contains `roles` with `Sites.*` application permissions).

Testing and troubleshooting
- After registering the app and granting admin consent, token permissions may take a few minutes to propagate. Use `decode-token.ps1` to inspect the token claims.
- If the Graph calls fail with permission errors, ensure the app has Application permissions (not Delegated) and admin consent was granted.
- Common errors and causes:
  - `generalException` when resolving site id: often permissions not yet propagated or incorrect site path formatting.
  - `BadRequest` with message mentioning `System.Collections.Hashtable`: usually caused by passing PowerShell objects incorrectly to the REST wrapper; scripts in this folder already convert bodies with `ConvertTo-Json` and call `Invoke-RestMethod` directly.
  - `nameAlreadyExists` when creating a list: script now handles this by locating the existing list or deleting it when `-Force` is used.

Security recommendations
- Store secrets securely (Key Vault, environment variables in CI/CD, or service principal certificates). Do not commit `.env` to source control.
- Use certificates for long-lived automation where possible.
- Limit application permissions to the minimum necessary and rotate secrets regularly.

Minimal PowerShell test (copy/paste)
```powershell
# load .env into process (simple)
Get-Content .\.env | ForEach-Object { if ($_ -match '^(\w+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2].Trim('"'), 'Process') } }
$tenant=$env:ENTRA_TENANT_ID; $clientId=$env:ENTRA_CLIENT_ID; $clientSecret=$env:ENTRA_CLIENT_SECRET
$tokenResp = Invoke-RestMethod -Method Post -Uri "https://login.microsoftonline.com/$tenant/oauth2/v2.0/token" -Body @{ client_id=$clientId; scope='https://graph.microsoft.com/.default'; client_secret=$clientSecret; grant_type='client_credentials' }
$token = $tokenResp.access_token
Invoke-RestMethod -Method Get -Uri "https://graph.microsoft.com/v1.0/sites/{host}:/sites/{sitePath}:" -Headers @{ Authorization = "Bearer $token" }
```

If you need a different workspace setup, copy `create-registrations-graph.ps1` and adjust the site URL and list names as needed.

References
- Microsoft identity platform: client credentials - https://learn.microsoft.com/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow
- Microsoft Graph Sites and Lists API - https://learn.microsoft.com/graph/api/resources/sharepoint?view=graph-rest-1.0
