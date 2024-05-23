<template>
  <v-card variant="tonal" max-width="500" width="auto" class="justify-center mx-auto" :loading="state === 'loading'"
    color="purple-lighten-4">
    <span v-if="state === 'idle'">
      <v-card-text class="pb-0" id="language-filter-card">
        <div class="text-medium-emphasis mb-2">
          <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-sim-outline</v-icon>
          Playlist URL / ID
        </div>
        <v-text-field placeholder="https://open.spotify.com/playlist/..." variant="outlined" spellcheck="false"
          v-model="playlistValue">
          <template #append-inner>
            <v-icon @mousedown.stop @click.stop @click="openLibrary" icon="mdi-open-in-new"></v-icon>
          </template>
        </v-text-field>


        <div class="text-medium-emphasis mb-2">
          <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-translate</v-icon>
          Keep Languages
        </div>

        <v-select chips label="Select languages to keep" :items="displaySupportedLanguages" multiple variant="outlined"
          v-model="selectedLanguages" id="rlate"></v-select>

        <div v-if="showCustomCharset">
          <div class="text-medium-emphasis mb-2">
            <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-chart-bubble</v-icon>
            Custom charset
          </div>
          <v-text-field placeholder="!@#$%^&*..." variant="outlined" spellcheck="false"
            v-model="supportedLanguages['custom']['charset']" density="compact"></v-text-field>
        </div>


      </v-card-text>

      <v-card-actions class="justify-center">
        <v-btn variant="text" prepend-icon="mdi-truck-fast" color="purple-lighten-2" size="large"
          @click="generatePlaylist">Generate</v-btn>
      </v-card-actions>
    </span>
    <span v-else-if="state === 'done'">
      <h2 class="done mt-5 mb-2 text-center">🎉 Done</h2>
      <PlaylistCard v-if="playlistId" :newDelay="true" :playlistId="playlistId"></PlaylistCard>

      <v-card-actions class="justify-center mt-5 flex-wrap">
        <v-btn color="green" variant="outlined" prepend-icon="mdi-spotify" class="ma-2" @click="openPlaylist">
          Open Playlist
        </v-btn>
        <v-btn color="blue" variant="outlined" prepend-icon="mdi-repeat" class="ma-2 justify-center"
          @click="state = 'idle'; playlistValue = '';">
          Another one
        </v-btn>
      </v-card-actions>
    </span>
    <span v-else-if="state === 'error'">
      <v-card-text>
        <v-alert variant="outlined" type="error" prominent border="top" style="font-size: 1rem;">
          {{ error }}
        </v-alert>
      </v-card-text>



      <v-card-actions class="justify-center mt-5 flex-wrap">
        <v-btn color="blue" variant="outlined" prepend-icon="mdi-repeat" class="ma-2 justify-center"
          @click="state = 'idle'; playlistValue = '';">
          Try again
        </v-btn>
      </v-card-actions>
    </span>
  </v-card>
</template>

<style>
@font-face {
  font-family: flagsFont;
  src: url(https://www.babelstone.co.uk/Fonts/WOFF/BabelStoneFlags.woff);
}

.v-list-item-title,
#language-filter-card .v-chip__content {
  font-family: flagsFont !important;
}
</style>

<script>
import PlaylistCard from '@/components/PlaylistCard.vue';


export default {
  components: {
    PlaylistCard
  },
  data() {
    return {
      supportedLanguages: {
        english: {
          flag: "🇺🇸",
          charset: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        },
        hebrew: {
          flag: "🇮🇱",
          charset: "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"
        },
        custom: {
          flag: "✨",
          charset: ""
        }
      },

      displaySupportedLanguages: [],
      displaySupportedLanguagesMap: {},

      selectedLanguages: [],

      showCustomCharset: false,

      playlistValue: "",


      // -------------------
      state: 'idle',  // idle, done, error

      playlistName: 'test',
      playlistId: '',
      playlistImage: 'https://img.freepik.com/premium-vector/cartoon-cute-cat-with-square-shape-square-icon-apps-games-vector-illustration-isolated_351178-23.jpg',
      playlistSongsCount: 0,
    };
  },
  created() {
    for (let [name, ln] of Object.entries(this.supportedLanguages)) {
      let dname;
      if (name === "custom") dname = "Custom charset"
      else dname = name.charAt(0).toUpperCase() + name.slice(1);

      let disp = `${ln.flag} ${dname}`;

      this.displaySupportedLanguages.push(disp);
      this.displaySupportedLanguagesMap[disp] = { name: name, ...ln };
    }

  },
  watch: {
    selectedLanguages() {
      const selected = this.selectedLanguages.map(disp => this.displaySupportedLanguagesMap[disp]);
      this.showCustomCharset = selected.some(ln => ln.name === "custom");
      console.log(this.selectedLanguages)
    },
    supportedLanguages: {
      handler() {
        let val = this.supportedLanguages["custom"].charset;
        this.displaySupportedLanguagesMap["✨ Custom charset"].charset = val
      },
      deep: true
    }
  },

  methods: {
    openPlaylist() {
      window.open(`spotify:user:spotify:playlist:${this.playlistId}`, '_blank')
    },

    async generatePlaylist() {
      this.$emit("start-loading");

      const charset = this.selectedLanguages.map(disp => this.displaySupportedLanguagesMap[disp].charset).join("");

      const js = await this.api.languageFilter({
        playlist: this.playlistValue,
        keep_chars: charset,
      });

      this.$emit("stop-loading");

      if (js.error) {
        this.$emit("display-error", js.error);
        return
      }

      this.playlistId = js.id;
      this.playlistName = js.name;
      this.playlistImage = js.image;
      this.playlistSongsCount = js.songs_count;
      this.state = 'done';
    },
    openLibrary() {
      window.open("spotify:library", '_blank')
    },
  },

}

</script>