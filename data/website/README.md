# Tesla Fleet API - Public Key Hosting

Denne mappen inneholder filene som må lastes opp til et offentlig nettsted for å registrere applikasjonen din med Tesla Fleet API.

## Hva som må lastes opp

Last opp **hele denne mappen** til et gratis hosting-tjeneste. Strukturen må være:

```
https://ditt-domene.com/
├── index.html
└── .well-known/
    └── appspecific/
        └── com.tesla.3p.public-key.pem
```

## Anbefalte Gratis Hosting-tjenester

### Vercel (Anbefalt - Enklest)

1. Gå til https://vercel.com
2. Sign up med GitHub, GitLab, eller Bitbucket
3. Klikk "Add New" → "Project"
4. Importer denne mappen
5. Deploy

Du får en URL som: `https://ditt-prosjekt.vercel.app`

### Netlify (Også Enkelt)

1. Gå til https://www.netlify.com
2. Sign up gratis
3. Dra og slipp denne `website` mappen til Netlify Drop
4. Deploy

Du får en URL som: `https://ditt-prosjekt.netlify.app`

### GitHub Pages (Hvis du har GitHub)

1. Lag et nytt repository på GitHub
2. Last opp filene fra denne mappen
3. Gå til Settings → Pages
4. Velg branch og enable GitHub Pages

Du får en URL som: `https://ditt-brukernavn.github.io/repo-navn`

## Etter Upload

1. Test at public key er tilgjengelig:
   ```
   https://ditt-domene.com/.well-known/appspecific/com.tesla.3p.public-key.pem
   ```

2. Gå til Tesla Developer Portal:
   https://developer.tesla.com/dashboard/app-details/e416ee82-7b17-44c7-9e8f-804da086d7ee

3. Oppdater "Allowed Origin URLs" til å inkludere ditt nye domene:
   ```
   https://ditt-domene.com
   ```

4. Kjør registrerings-scriptet igjen:
   ```bash
   python scripts/register_tesla_account.py
   ```

## Viktig!

- Den offentlige nøkkelen (com.tesla.3p.public-key.pem) er trygg å dele
- Den private nøkkelen (data/keys/private_key.pem) må ALDRI deles eller lastes opp
