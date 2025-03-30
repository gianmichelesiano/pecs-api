# Test dell'upload di immagini con Supabase

Questo documento fornisce esempi su come testare l'upload di immagini utilizzando gli endpoint API.

## Prerequisiti

- Il server API è in esecuzione su `http://localhost:8000`
- Hai configurato Supabase con il bucket 'pecs'
- Hai un'immagine di test da caricare

## 1. Verifica dello stato di Supabase

Prima di testare l'upload, puoi verificare lo stato della connessione a Supabase:

```bash
curl -X GET "http://localhost:8000/api/v1/images/supabase-status"
```

Questo endpoint restituirà informazioni dettagliate sulla connessione a Supabase, incluso se il bucket 'pecs' è accessibile.

## 2. Test dell'upload senza autenticazione

Puoi testare l'upload di un'immagine senza autenticazione utilizzando l'endpoint di test:

```bash
curl -X POST "http://localhost:8000/api/v1/images/test-upload" \
  -F "file=@/percorso/alla/tua/immagine.jpg"
```

Sostituisci `/percorso/alla/tua/immagine.jpg` con il percorso alla tua immagine di test.

Se l'upload ha successo, riceverai una risposta simile a:

```json
{
  "success": true,
  "message": "Image uploaded successfully",
  "url": "https://ypsljlrzdpkibowewidv.supabase.co/storage/v1/object/public/pecs/123e4567-e89b-12d3-a456-426614174000.jpeg"
}
```

## 3. Test dell'upload con l'endpoint principale

Ora puoi utilizzare direttamente l'endpoint principale senza autenticazione (in ambiente locale):

```bash
curl -X POST "http://localhost:8000/api/v1/images/upload" \
  -F "file=@/percorso/alla/tua/immagine.jpg" \
  -F "description=La mia immagine di test"
```

Sostituisci `/percorso/alla/tua/immagine.jpg` con il percorso alla tua immagine di test.

Se sei in un ambiente di produzione o vuoi testare con autenticazione, devi prima ottenere un token di accesso:

```bash
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=tua_email@esempio.com&password=tua_password"
```

Sostituisci `tua_email@esempio.com` e `tua_password` con le tue credenziali.

Poi, utilizza il token di accesso per caricare un'immagine:

```bash
curl -X POST "http://localhost:8000/api/v1/images/upload" \
  -H "Authorization: Bearer TUO_TOKEN_DI_ACCESSO" \
  -F "file=@/percorso/alla/tua/immagine.jpg" \
  -F "description=La mia immagine di test"
```

Sostituisci `TUO_TOKEN_DI_ACCESSO` con il token ottenuto nel passaggio precedente.

## 4. Test con Postman o Insomnia

Se preferisci utilizzare un'interfaccia grafica, puoi utilizzare Postman o Insomnia:

1. Crea una nuova richiesta POST a `http://localhost:8000/api/v1/images/test-upload`
2. Nella sezione "Body", seleziona "form-data"
3. Aggiungi un campo "file" di tipo "File" e seleziona la tua immagine
4. Invia la richiesta

## Risoluzione dei problemi

Se riscontri errori durante l'upload, controlla la risposta dell'endpoint di test per suggerimenti sulla risoluzione dei problemi. Potresti dover configurare le policy RLS in Supabase come descritto nel file `supabase-setup-instructions.md`.
