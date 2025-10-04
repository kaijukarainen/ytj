"""
Application configuration
"""

BUSINESS_LINES = [
    # A - MAATALOUS, METSÄTALOUS JA KALATALOUS
    {"code": "01", "name": "Kasvinviljely ja kotieläintalous, riistatalous ja niihin liittyvät palvelut"},
    {"code": "02", "name": "Metsätalous ja puunkorjuu"},
    {"code": "03", "name": "Kalastus ja vesiviljely"},
    
    # B - KAIVOSTOIMINTA JA LOUHINTA
    {"code": "05", "name": "Kivihiilen ja ruskohiilen kaivu"},
    {"code": "06", "name": "Raakaöljyn ja maakaasun tuotanto"},
    {"code": "07", "name": "Metallimalmien louhinta"},
    {"code": "08", "name": "Muu kaivostoiminta ja louhinta"},
    {"code": "09", "name": "Kaivostoimintaa palveleva toiminta"},
    
    # C - TEOLLISUUS
    {"code": "10", "name": "Elintarvikkeiden valmistus"},
    {"code": "11", "name": "Juomien valmistus"},
    {"code": "12", "name": "Tupakkatuotteiden valmistus"},
    {"code": "13", "name": "Tekstiilien valmistus"},
    {"code": "14", "name": "Vaatteiden valmistus"},
    {"code": "15", "name": "Nahan ja nahkatuotteiden valmistus"},
    {"code": "16", "name": "Sahatavaran sekä puu- ja korkkituotteiden valmistus"},
    {"code": "17", "name": "Paperin, paperi- ja kartonkituotteiden valmistus"},
    {"code": "18", "name": "Painaminen ja tallenteiden jäljentäminen"},
    {"code": "19", "name": "Koksin ja jalostettujen öljytuotteiden valmistus"},
    {"code": "20", "name": "Kemikaalien ja kemiallisten tuotteiden valmistus"},
    {"code": "21", "name": "Lääkeaineiden ja lääkkeiden valmistus"},
    {"code": "22", "name": "Kumi- ja muovituotteiden valmistus"},
    {"code": "23", "name": "Muiden ei-metallisten mineraalituotteiden valmistus"},
    {"code": "24", "name": "Metallien jalostus"},
    {"code": "25", "name": "Metallituotteiden valmistus"},
    {"code": "26", "name": "Tietokoneiden sekä elektronisten ja optisten tuotteiden valmistus"},
    {"code": "27", "name": "Sähkölaitteiden valmistus"},
    {"code": "28", "name": "Muiden koneiden ja laitteiden valmistus"},
    {"code": "29", "name": "Moottoriajoneuvojen, perävaunujen ja puoliperävaunujen valmistus"},
    {"code": "30", "name": "Muiden kulkuneuvojen valmistus"},
    {"code": "31", "name": "Huonekalujen valmistus"},
    {"code": "32", "name": "Muu valmistus"},
    {"code": "33", "name": "Koneiden ja laitteiden korjaus, huolto ja asennus"},
    
    # D - SÄHKÖ-, KAASU- JA LÄMPÖHUOLTO
    {"code": "35", "name": "Sähkö-, kaasu- ja lämpöhuolto, jäähdytysliiketoiminta"},
    
    # E - VESIHUOLTO, VIEMÄRI- JA JÄTEVESIHUOLTO
    {"code": "36", "name": "Veden otto, puhdistus ja jakelu"},
    {"code": "37", "name": "Viemäri- ja jätevesihuolto"},
    {"code": "38", "name": "Jätteen keruu, käsittely ja loppusijoitus"},
    {"code": "39", "name": "Maaperän ja vesistöjen kunnostus"},
    
    # F - RAKENTAMINEN
    {"code": "41", "name": "Talonrakentaminen"},
    {"code": "42", "name": "Maa- ja vesirakentaminen"},
    {"code": "43", "name": "Erikoistunut rakennustoiminta"},
    
    # G - TUKKU- JA VÄHITTÄISKAUPPA
    {"code": "45", "name": "Moottoriajoneuvojen kauppa, korjaus ja huolto"},
    {"code": "46", "name": "Tukkukauppa"},
    {"code": "47", "name": "Vähittäiskauppa"},
    
    # H - KULJETUS JA VARASTOINTI
    {"code": "49", "name": "Maaliikenne ja putkijohtokuljetus"},
    {"code": "50", "name": "Vesiliikenne"},
    {"code": "51", "name": "Ilmaliikenne"},
    {"code": "52", "name": "Varastointi ja liikennettä palveleva toiminta"},
    {"code": "53", "name": "Posti- ja kuriiritoiminta"},
    
    # I - MAJOITUS- JA RAVITSEMISTOIMINTA
    {"code": "55", "name": "Majoitus"},
    {"code": "56", "name": "Ravitsemistoiminta"},
    
    # J - INFORMAATIO JA VIESTINTÄ
    {"code": "58", "name": "Kustannustoiminta"},
    {"code": "59", "name": "Elokuva-, video- ja televisio-ohjelmatuotanto, äänitteiden ja musiikin kustantaminen"},
    {"code": "60", "name": "Radio- ja televisiotoiminta"},
    {"code": "61", "name": "Televiestintä"},
    {"code": "62", "name": "Ohjelmistot, konsultointi ja siihen liittyvä toiminta"},
    {"code": "6201", "name": "Ohjelmistojen suunnittelu ja valmistus"},
    {"code": "6202", "name": "Tietokoneiden konsultointi"},
    {"code": "6209", "name": "Muut tietotekniikkapalvelut"},
    {"code": "63", "name": "Tietopalvelutoiminta"},
    
    # K - RAHOITUS- JA VAKUUTUSTOIMINTA
    {"code": "64", "name": "Rahoituspalvelut"},
    {"code": "65", "name": "Vakuutus-, jälleenvakuutus- ja eläkevakuutustoiminta"},
    {"code": "66", "name": "Rahoitusta ja vakuuttamista palveleva toiminta"},
    
    # L - KIINTEISTÖALAN TOIMINTA
    {"code": "68", "name": "Kiinteistöalan toiminta"},
    
    # M - AMMATILLINEN, TIETEELLINEN JA TEKNINEN TOIMINTA
    {"code": "69", "name": "Lakiasiain- ja laskentatoimen palvelut"},
    {"code": "70", "name": "Pääkonttorien toiminta; liikkeenjohdon konsultointi"},
    {"code": "71", "name": "Arkkitehti- ja insinööripalvelut; tekninen testaus ja analysointi"},
    {"code": "72", "name": "Tieteellinen tutkimus ja kehittäminen"},
    {"code": "73", "name": "Mainostoiminta ja markkinatutkimus"},
    {"code": "74", "name": "Muut erikoistuneet palvelut liike-elämälle"},
    {"code": "75", "name": "Eläinlääkintäpalvelut"},
    
    # N - HALLINTO- JA TUKIPALVELUTOIMINTA
    {"code": "77", "name": "Vuokraus- ja leasingtoiminta"},
    {"code": "78", "name": "Työllistämistoiminta"},
    {"code": "79", "name": "Matkatoimistojen ja matkanjärjestäjien toiminta; varauspalvelut"},
    {"code": "80", "name": "Turvallisuus-, vartiointi- ja etsiväpalvelut"},
    {"code": "81", "name": "Kiinteistön- ja maisemanhoito"},
    {"code": "82", "name": "Hallinto- ja tukipalvelut liike-elämälle"},
    
    # O - JULKINEN HALLINTO JA MAANPUOLUSTUS
    {"code": "84", "name": "Julkinen hallinto ja maanpuolustus; pakollinen sosiaalivakuutus"},
    
    # P - KOULUTUS
    {"code": "85", "name": "Koulutus"},
    
    # Q - TERVEYS- JA SOSIAALIPALVELUT
    {"code": "86", "name": "Terveyspalvelut"},
    {"code": "86230", "name": "Hammaslääkäripalvelut"},
    {"code": "87", "name": "Sosiaalihuollon laitospalvelut"},
    {"code": "88", "name": "Sosiaalihuollon avopalvelut"},
    
    # R - TAITEET, VIIHDE JA VIRKISTYS
    {"code": "90", "name": "Kulttuuri- ja viihdetoiminta"},
    {"code": "91", "name": "Kirjastojen, arkistojen, museoiden ja muiden kulttuurilaitosten toiminta"},
    {"code": "92", "name": "Rahapeli- ja vedonlyöntitoiminta"},
    {"code": "93", "name": "Urheilutoiminta sekä huvi- ja virkistyspalvelut"},
    
    # S - MUU PALVELUTOIMINTA
    {"code": "94", "name": "Järjestöjen toiminta"},
    {"code": "95", "name": "Tietokoneiden, henkilökohtaisten ja kotitaloustavaroiden korjaus"},
    {"code": "96", "name": "Muut henkilökohtaiset palvelut"},
    
    # T - KOTITALOUKSIEN TOIMINTA
    {"code": "97", "name": "Kotitalouksien toiminta kotitaloustyöntekijöiden työnantajina"},
    {"code": "98", "name": "Kotitalouksien eriyttämätön toiminta tavaroiden ja palvelujen tuottamiseksi omaan käyttöön"},
    
    # U - KANSAINVÄLISTEN ORGANISAATIOIDEN TOIMINTA
    {"code": "99", "name": "Kansainvälisten organisaatioiden ja toimielinten toiminta"}
]