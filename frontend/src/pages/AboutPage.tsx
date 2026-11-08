import { Link } from 'react-router'
import { BRAND } from '../lib/brand'

export function AboutPage() {
  return (
    <>
      <h1>O alatu i metodologiji</h1>
      <p className="lead">
        {BRAND.name} spaja otvorene podatke o okolišu, prostoru i uslugama u jedan pregled za
        jednu adresu. Namijenjen je kupcima i najmoprimcima koji žele znati više prije nego što
        potpišu ugovor.
      </p>
      <p className="disclaimer">
        Ovo je informativni alat, a ne službena procjena rizika, geodetski ni građevinski
        pregled. Ne zamjenjuje karte i upozorenja Hrvatskih voda, DHMZ-a i civilne zaštite.
      </p>

      <section className="section" aria-labelledby="principles">
        <h2 id="principles">Načela</h2>
        <ul>
          <li>
            Svaka kategorija ima vlastito, razumljivo značenje. „Skor za život” je prosjek
            podskorova kategorija s vidljivim i podesivim težinama; nijedna težina nije skrivena,
            a vrijednosti kategorija se ne mijenjaju.
          </li>
          <li>
            Svaka vrijednost ima izvor, datum i vrstu: <strong>izmjereno</strong> (mjerenje,
            vozni red ili registar), <strong>modelirano</strong> (izračun modelom) ili{' '}
            <strong>procjena</strong> (zamjenski podatak).
          </li>
          <li>
            Profil (obitelj, umirovljenik, student, rad od kuće ili vlastiti) mijenja redoslijed,
            naglasak i težine u skoru, nikad vrijednosti.
          </li>
          <li>„Nema podataka” uvijek se prikazuje; kategorija se nikad tiho ne izostavlja.</li>
          <li>
            Sažetak i odgovori asistenta slažu se iz predložaka nad izračunima; jezični model ne
            smišlja brojke.
          </li>
        </ul>
      </section>

      <section className="section" aria-labelledby="thresholds">
        <h2 id="thresholds">Kategorije i pragovi</h2>
        <div style={{ overflowX: 'auto' }}>
          <table className="place-table">
            <caption className="visually-hidden">Kategorije, način izračuna i pragovi s izvorom</caption>
            <thead>
              <tr>
                <th scope="col">Kategorija</th>
                <th scope="col">Kako se računa</th>
                <th scope="col">Prag i izvor</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">Poplave</th>
                <td>
                  Dubina vode na točki i u krugu od 100 m iz JRC karata riječnih poplava (oko 90
                  m) za povratna razdoblja od 10, 100 i 500 godina.
                </td>
                <td>
                  Loše: točka je u području od 10 ili 100 godina (velika i srednja vjerojatnost).
                  Upozorenje: područje od 500 godina ili poplavno područje unutar 100 m. Scenariji
                  prema opisu karata opasnosti od poplava Hrvatskih voda.
                </td>
              </tr>
              <tr>
                <th scope="row">Kvaliteta zraka</th>
                <td>Godišnji prosjek PM2,5 i NO2 iz interpoliranih karata EEA-e za 2024. (1 km).</td>
                <td>
                  Ocjena zraka, lošija od ocjena za PM2,5 i NO2: vrlo dobar do smjernice WHO-a
                  (PM2,5 5, NO2 10 µg/m³), dobar do granice EU-a za 2030. (10 i 20), umjeren do
                  granice EU-a koja vrijedi danas (25 i 40, Direktiva (EU) 2024/2881), loš iznad
                  toga.
                </td>
              </tr>
              <tr>
                <th scope="row">Zelenilo i hlad</th>
                <td>
                  Udio drveća, zelenih i izgrađenih površina u kopnu u krugu od 300 m (ESA
                  WorldCover 2021., 10 m; more se ne broji) i najbliži park (OpenStreetMap).
                  Temperaturu ne mjerimo: drveće je pokazatelj hlada.
                </td>
                <td>
                  Pravilo 3-30-300 (Konijnendijk, 2023.): najmanje 30 % krošnji i javna zelena
                  površina do 300 m. Dobro: oba uvjeta; upozorenje: jedan; loše: nijedan.
                </td>
              </tr>
              <tr>
                <th scope="row">Udaljenost od prometnica</th>
                <td>
                  Zračna udaljenost od lokacije do autocesta, brzih, državnih i glavnih gradskih cesta te
                  pruga (OpenStreetMap); županijske ceste s oznakom Ž se ne broje. Za naselje se
                  računa za svaku adresu. Ne mjerimo buku; to je zamjenski pokazatelj.
                </td>
                <td>
                  Do 300 m: blizu prometnice; 300–500 m: rub zone prometa; dalje: podalje od
                  prometnica (zona utjecaja prometa prema pregledu Health Effects Institutea,
                  2010.).
                </td>
              </tr>
              <tr>
                <th scope="row">Požari raslinja</th>
                <td>
                  Opožarene površine u krugu od 2 km od 2016. iz europskog sustava EFFIS
                  (satelitsko kartiranje).
                </td>
                <td>Informacija (nema službenog praga). Prošli požari pokazuju izloženost, a ne predviđaju buduće.</td>
              </tr>
              <tr>
                <th scope="row">Sunce na krovu</th>
                <td>JRC PVGIS 5.3: godišnja proizvodnja za 1 kW snage uz optimalni nagib i 14 % gubitaka.</td>
                <td>Informacija (nema službenog praga).</td>
              </tr>
              <tr>
                <th scope="row">Život bez auta</th>
                <td>
                  Koliko od sedam svakodnevnih potreba je unutar 15 minuta hoda po mreži ulica
                  (Valhalla nad OpenStreetMapom, 4,5 km/h).
                </td>
                <td>Informacija; prikazuje se „X od 7” i što nedostaje.</td>
              </tr>
              <tr>
                <th scope="row">Javni prijevoz</th>
                <td>
                  Stajališta unutar 10 minuta hoda; prosječan broj polazaka na sat od 6 do 20 sati
                  radnim danom iz voznih redova ZET-a, HŽPP-a i Autotroleja.
                </td>
                <td>Informacija. Drugdje stajališta iz OpenStreetMapa „bez voznog reda”.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section" aria-labelledby="privacy">
        <h2 id="privacy">Privatnost</h2>
        <p>
          Upisane adrese i pitanja asistentu ne spremaju se i ne bilježe. Nema kolačića za
          praćenje ni analitike. Fontovi se poslužuju s našeg poslužitelja.
        </p>
      </section>

      <section className="section" aria-labelledby="more">
        <h2 id="more">Više</h2>
        <p>
          Popis svih izvora s licencama na stranici <Link to="/izvori">Izvori</Link>. Otvoreni API
          s OpenAPI opisom: <a href="/api/docs">/api/docs</a>. Detaljna metodologija, arhitektura i
          odluke nalaze se u mapi <code>docs/</code> repozitorija.
        </p>
      </section>
    </>
  )
}
