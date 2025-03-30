# Configurazione Supabase per l'upload di immagini

Questo documento fornisce istruzioni su come configurare Supabase per consentire l'upload di immagini nell'applicazione PECS.

## 1. Creare un bucket in Supabase Storage

1. Accedi al tuo progetto Supabase: https://app.supabase.io
2. Vai alla sezione "Storage" nel menu laterale
3. Clicca su "Create a new bucket"
4. Inserisci il nome del bucket: `pecs` (o il nome che hai configurato in `.env`)
5. Seleziona "Public" per rendere il bucket pubblico
6. Clicca su "Create bucket"

## 2. Configurare le policy RLS (Row-Level Security)

Per consentire l'upload e l'accesso pubblico ai file utilizzando una chiave API anonima, devi configurare le policy RLS per il bucket:

1. Nella sezione "Storage", seleziona il bucket `pecs`
2. Vai alla scheda "Policies"
3. Clicca su "New Policy" (Nuova policy)

### Policy per l'accesso pubblico completo

1. Nella schermata "Adding new policy to pecs":
   - Dai un nome alla policy, ad esempio: "Public access"
   - Seleziona TUTTE le operazioni: SELECT, INSERT, UPDATE, DELETE
   - Nella sezione "Target roles", lascia l'impostazione predefinita "Defaults to all (public) roles if none selected"
   - Nella sezione "Policy definition", inserisci semplicemente:
     ```sql
     true
     ```
   - Clicca su "Review" e poi "Save policy"

Questa policy consentirà a tutti gli utenti (inclusi quelli anonimi) di eseguire tutte le operazioni sul bucket "pecs".

### Configurare il bucket come pubblico

Oltre alle policy RLS, assicurati che il bucket sia configurato come pubblico:

1. Nella sezione "Storage", seleziona il bucket `pecs`
2. Clicca su "Settings" (Impostazioni)
3. Assicurati che l'opzione "Public" sia selezionata
4. Clicca su "Save" (Salva)

### Configurare le policy a livello di tabella

Oltre alle policy del bucket, potrebbe essere necessario configurare le policy a livello di tabella:

1. Vai alla sezione "Authentication" > "Policies" nel menu laterale
2. Seleziona la tabella "objects" nello schema "storage"
3. Clicca su "New Policy" (Nuova policy)
4. Nella schermata "Create a new policy":
   - Dai un nome alla policy, ad esempio: "Public access to objects"
   - Seleziona "Custom policy" come tipo di policy
   - Seleziona TUTTE le operazioni: SELECT, INSERT, UPDATE, DELETE
   - Nella sezione "Policy definition", inserisci:
     ```sql
     true
     ```
   - Clicca su "Save policy" (Salva policy)

### Verificare le impostazioni di CORS

Se stai riscontrando problemi con l'accesso ai file, potrebbe essere necessario configurare le impostazioni CORS:

1. Nella sezione "Storage", clicca su "Policies" nel menu laterale
2. Scorri verso il basso fino alla sezione "CORS"
3. Aggiungi la seguente configurazione:
   ```json
   {
     "AllowedOrigins": ["*"],
     "AllowedMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     "AllowedHeaders": ["*"],
     "MaxAgeSeconds": 3000,
     "ExposeHeaders": []
   }
   ```
4. Clicca su "Save" (Salva)

## 3. Utilizzare una chiave API di servizio (alternativa alle policy RLS)

Se continui a riscontrare problemi con le policy RLS, puoi utilizzare una chiave API di servizio che ha privilegi più elevati:

1. Vai alla sezione "Project Settings" > "API" nel menu laterale
2. Nella sezione "Project API keys", copia la "service_role key" (NON la "anon" key)
3. Aggiorna il file `.env` sostituendo la chiave anonima con la chiave di servizio:
   ```
   SUPABASE_KEY=your-service-role-key
   ```

**Nota di sicurezza**: La chiave di servizio ha accesso completo al tuo progetto Supabase, inclusi tutti i dati. Utilizzala solo in ambienti sicuri e non includerla mai nel codice client.

## 4. Testare l'upload di immagini

Dopo aver configurato le policy RLS o utilizzato una chiave di servizio, puoi testare l'upload di immagini utilizzando gli endpoint:

1. Endpoint di diagnostica (verifica la connessione a Supabase):
   ```
   GET http://localhost:8000/api/v1/images/supabase-status
   ```

2. Endpoint di test (senza autenticazione):
   ```
   POST http://localhost:8000/api/v1/images/test-upload
   ```
   Con un form multipart contenente un'immagine nel campo `file`.

3. Endpoint principale (con autenticazione):
   ```
   POST http://localhost:8000/api/v1/images/upload
   ```
   Con header `Authorization: Bearer YOUR_ACCESS_TOKEN` e un form multipart.

## Risoluzione dei problemi comuni

### Errore: "Bucket 'pecs' does not exist"

Se ricevi questo errore anche se hai creato il bucket:

1. Verifica che il nome del bucket in `.env` corrisponda esattamente al nome del bucket in Supabase (incluse maiuscole/minuscole)
2. Controlla che la chiave API in `.env` abbia le autorizzazioni necessarie per accedere al bucket
3. Prova a utilizzare una chiave API di servizio invece di una chiave anonima

### Errore: "new row violates row-level security policy"

Questo errore indica che le policy RLS non sono configurate correttamente:

1. Verifica di aver creato una policy che consente l'operazione INSERT
2. Assicurati che la policy sia impostata su `true` per consentire a tutti di caricare file
3. Se stai utilizzando una chiave anonima, prova a utilizzare una chiave di servizio

### Errore: "403 Forbidden"

Questo errore indica un problema di autorizzazione:

1. Verifica che le policy RLS siano configurate correttamente
2. Prova a utilizzare una chiave API di servizio invece di una chiave anonima
3. Assicurati che il bucket sia impostato come "Public" nelle impostazioni del bucket

## Utilizzo degli URL firmati

L'applicazione ora utilizza URL firmati per accedere alle immagini in Supabase Storage. Questi URL contengono un token di accesso che consente di bypassare le policy RLS e accedere direttamente ai file.

### Vantaggi degli URL firmati

1. **Accesso garantito**: Gli URL firmati funzionano anche se le policy RLS non sono configurate correttamente
2. **Sicurezza**: Solo chi ha l'URL firmato può accedere al file
3. **Controllo della scadenza**: È possibile impostare una data di scadenza per l'URL

### Come funzionano gli URL firmati

1. Quando un'immagine viene caricata o richiesta, l'applicazione genera un URL firmato utilizzando la chiave API di Supabase
2. L'URL firmato contiene un token di accesso che consente di accedere al file
3. L'URL firmato ha una scadenza molto lunga (10 anni), quindi è praticamente permanente

### Limitazioni degli URL firmati

1. **Dimensione dell'URL**: Gli URL firmati sono più lunghi degli URL pubblici
2. **Scadenza**: Anche se impostata a 10 anni, gli URL firmati alla fine scadranno
3. **Dipendenza dalla chiave API**: Se la chiave API viene revocata, gli URL firmati non funzioneranno più

Se preferisci utilizzare URL pubblici invece di URL firmati, puoi modificare il codice in `app/services/supabase_storage.py` e `app/api/routes/images.py` per utilizzare solo il metodo `get_public_url` invece di `create_signed_url`.
