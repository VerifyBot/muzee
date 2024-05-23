c<template>
  <v-card variant="tonal" max-width="500" width="auto" class="justify-center mx-auto" :loading="state === 'loading'"
    color="purple-lighten-4">
    <span v-if="state === 'idle'">
      <v-card-text class="pb-0">
        <div class="text-medium-emphasis mb-2">
          <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-script-text</v-icon>
          Playlist Topic
        </div>
        <v-text-field placeholder="eurovision songs..." variant="outlined" spellcheck="false"
          v-model="topicValue">
          <template #append-inner>
            <v-icon @mousedown.stop @click.stop @click="randomTopic" icon="mdi-shuffle-variant"></v-icon>
          </template>
        </v-text-field>


        <div class="text-medium-emphasis mb-2">
          <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-library</v-icon>
          Songs Count
          <span class="time-picked ml-2" style="font-size: 1.7rem" v-text="songsCount"></span>
        </div>
        <v-slider v-model="songsCount" step="5" min="5" max="100" color="purple-lighten-2">

        </v-slider>


      </v-card-text>

      <v-card-actions class="justify-center">
        <v-btn variant="text" prepend-icon="mdi-truck-fast" color="purple-lighten-2" size="large"
          @click="generatePlaylist">Generate</v-btn>
      </v-card-actions>
    </span>
    <span v-else-if="state === 'done'">
      <h2 class="done mt-5 mb-2 text-center">🎉 Done</h2>

      <PlaylistCard v-if="playlistId" :newDelay="true" :playlistId="playlistId" />

      <v-card-actions class="justify-center mt-5 flex-wrap">
        <v-btn color="green" variant="outlined" prepend-icon="mdi-spotify" class="ma-2" @click="openPlaylist">
          Open Playlist
        </v-btn>
        <v-btn color="blue" variant="outlined" prepend-icon="mdi-repeat" class="ma-2 justify-center"
          @click="state = 'idle'; topicValue = ''; songsCount = 50">
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
          @click="state = 'idle'; topicValue = ''; songsCount = 50">
          Try again
        </v-btn>
      </v-card-actions>
    </span>
  </v-card>
</template>

<script>
import PlaylistCard from '@/components/PlaylistCard.vue';


export default {
  components: {
    PlaylistCard
  },
  data() {
    return {
      direction: 'ltr',
      topicValue: "",
      songsCount: 50,

      state: 'idle',  // idle, loading, done, error
      loadingText: '',

      playlistName: 'test',
      playlistId: '',
      playlistImage: 'https://img.freepik.com/premium-vector/cartoon-cute-cat-with-square-shape-square-icon-apps-games-vector-illustration-isolated_351178-23.jpg',
      playlistSongsCount: 0,
    };
  },

  mounted() {
    console.log("IM MOUNTED!")
  },

  methods: {
    detectLanguageDirection() {
      const containsHebrew = /[\u0590-\u05FF]/.test(this.topicValue[0]);
      this.direction = containsHebrew ? 'rtl' : 'ltr';
    },
    openPlaylist() {
      window.open(`spotify:user:spotify:playlist:${this.playlistId}`, '_blank')
    },

    async generatePlaylist() {
      this.$emit("start-loading");

      const js = await this.api.generatePlaylist({
        topic: this.topicValue,
        songs_count: this.songsCount,
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


    async sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },

    randomTopic() {
      const topics = ["chill", "summer", "road trip", "feel good", "heartbreak", "motivation", "dance party", "throwback hits", "acoustic", "rainy day", "love songs", "energetic", "soulful", "indie", "electronic", "coffee shop", "mellow", "romantic evening", "pump up", "country", "jazz", "classical", "rap", "reggae", "alternative", "instrumental", "90s", "party anthem", "bass", "folk", "piano", "edm", "gospel", "rock", "latin", "funky", "calm", "80s", "blues", "upbeat", "soothing", "dubstep", "opera", "disco", "african", "guitar", "synthwave", "hip hop", "ska", "asian fusion", "punk", "world", "metal", "chilled electronica", "r&b", "salsa", "ambient", "pop", "trippy", "motown", "vocal harmony", "trap", "irish", "bluegrass", "epic orchestral", "funkadelic", "sitar", "psychedelic", "brazilian", "hawaiian", "tropical", "sufi", "acapella", "french", "caribbean", "scandinavian", "vibraphone", "japanese", "spanish", "russian", "aussie", "middle eastern", "bollywood", "canadian", "hiphop", "nordic", "tango", "gothic", "african safari", "indigenous", "celtic", "polynesian", "surf's up", "retro rewind", "fusion", "classical crossover", "mardi gras", "cinematic", "kaleidoscope", "dreamy drift", "mystical", "synesthetic", "digital", "uplifting", "jungle", "oceanic", "starlit symphony", "alien", "future funk", "robotic", "cyberpunk", "steampunk", "time traveler's", "neon nights", "interstellar", "celestial", "parallel universe", "quantum quest", "cosmic chill", "zen zone", "mindful", "yoga", "serenity", "tranquil trails", "healing", "nature's lullaby", "meditative mantras", "winter vibes", "lofi", "skateboard", "snow", "sleep", "energetic", "rock", "rap"];

      // between 1 to 3 topics
      const topicsCount = Math.floor(Math.random() * 3) + 1;
      const randomTopics = [];
      for (let i = 0; i < topicsCount; i++) {
        const randomTopic = topics[Math.floor(Math.random() * topics.length)];
        if (!randomTopics.includes(randomTopic)) {
          randomTopics.push(randomTopic);
        }
      }
      this.topicValue = randomTopics.join(", ");
    }

  },

}

</script>