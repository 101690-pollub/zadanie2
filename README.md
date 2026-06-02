### 1. Inicjalizacja i konfiguracja środowiska wieloplatformowego

Pobranie kodu źródłowego oraz uruchomienie emulatorów QEMU i Buildx. Umożliwia to kompilację obrazu na różne architektury procesorów (amd64 oraz arm64).

```yaml
      - name: Checkout source code
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

```

---

### 2. Logowanie do zewnętrznych rejestrów

Potok automatycznie uwierzytelnia się w serwisie Docker Hub oraz w ghcr.io, gdzie zostanie opublikowany gotowy obraz.

```yaml
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

```

---

### 3. Przygotowanie unikalnych znaczników (tagów)

Nazwa repozytorium jest automatycznie konwertowana do małych liter, a także generowany jest unikalny tag na podstawie skrótu commitu Git SHA.

```yaml
      - name: Prepare image tags
        id: prep
        run: |
          IMAGE=$(echo "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}" | tr '[:upper:]' '[:lower:]')
          echo "image=$IMAGE" >> $GITHUB_OUTPUT
          echo "sha_tag=sha-${GITHUB_SHA}" >> $GITHUB_OUTPUT

```

---

### 4. Budowa obrazu testowego z użyciem pamięci podręcznej

Obraz jest budowany lokalnie na jedną architekturę (linux/amd64) i ładowany do systemu w celu przeprowadzenia testów. Wykorzystywany jest zaawansowany zapis i odczyt cache w trybie mode=max na Docker Hubie.

```yaml
      - name: Build image for security scan
        uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64
          load: true
          tags: local-scan-image:latest
          cache-from: type=registry,ref=${{ env.CACHE_IMAGE }}
          cache-to: type=registry,ref=${{ env.CACHE_IMAGE }},mode=max

```

---

### 5. Instalacja narzędzia Trivy i test bezpieczeństwa CVE

Instalowany jest skaner Trivy. Następuje weryfikacja obrazu pod kątem podatności. Parametr --exit-code 1 w połączeniu z --severity HIGH,CRITICAL gwarantuje, że wykrycie poważnych błędów natychmiast zatrzyma potok i zablokuje dalsze kroki.

```yaml
      - name: Install Trivy
        run: |
          sudo apt-get update
          sudo apt-get install -y wget
          wget -qO- [https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh](https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh) | sh
          sudo mv ./bin/trivy /usr/local/bin/

      - name: Scan image with Trivy
        run: |
          trivy image \
            --severity HIGH,CRITICAL \
            --ignore-unfixed \
            --exit-code 1 \
            local-scan-image:latest

```

---

### 6. Publikacja obrazu wieloplatformowego

Po pomyślnym przejściu skanowania bezpieczeństwa, obraz jest kompilowany na dwie platformy (linux/amd64,linux/arm64) i wysyłany do ghcr.io z dwoma tagami (latest oraz sha-...).

```yaml
      - name: Build and push multi-platform image
        uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ${{ steps.prep.outputs.image }}:latest
            ${{ steps.prep.outputs.image }}:${{ steps.prep.outputs.sha_tag }}
          cache-from: type=registry,ref=${{ env.CACHE_IMAGE }}
          cache-to: type=registry,ref=${{ env.CACHE_IMAGE }},mode=max

```

---

### 7. Uzasadnienie schematu tagowania

* Tag `:latest` wskazuje na ostatnią stabilną wersję aplikacji.
* Tag `:sha-...` powiązuje dany obraz z konkretną zmianą w kodzie źródłowym.

Takie rozwiązanie pozwala łatwo pobrać najnowszą wersję oraz jednoznacznie zidentyfikować obraz powiązany z konkretną wersją kodu. W środowiskach produkcyjnych zapobiega to nadpisaniu działającej wersji w przypadku awarii (umożliwia natychmiastowy rollback).

---

### 8. Potwierdzenie działania

Workflow został uruchomiony poprawnie w GitHub Actions, a obraz został opublikowany do GHCR po pozytywnym przejściu skanowania bezpieczeństwa. Automatycznie wygenerowane podsumowanie procesu budowania (*Docker Build Summary*) potwierdza prawidłowe ładowanie danych cache oraz poprawną strukturę manifestu wieloplatformowego dla systemów `amd64` oraz `arm64`.

```
