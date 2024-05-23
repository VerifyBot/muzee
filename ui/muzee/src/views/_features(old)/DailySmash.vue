<template>
  <v-card variant="tonal" max-width="500" width="auto" class="justify-center mx-auto" :loading="state === 'loading'">
    <template v-slot:title>
      <div>
        🎴 Daily Smash
        <span style="color: rgb(75, 127, 195)" v-if="state === 'loading'"> (ON IT)</span>
        <span style="color: rgb(219, 102, 19)" v-else-if="state === 'error'"> (SAD)</span>
        <span style="color: rgb(75, 195, 75)" v-else-if="smashEnabled"> (ON)</span>
        <span style="color: rgb(166, 30, 30)" v-else> (OFF)</span>
      </div>
    </template>

    <span v-if="state === 'idle'">
      <v-divider class="mt-1 mb-4"></v-divider>

      <v-alert variant="default" class="px-1 py-0">
        <template v-slot:title>
          <div class="px-2">
            <span><v-icon color="secondary" style="vertical-align: text-bottom;">mdi-hours-24</v-icon> Run daily at</span>
            <span class="time-picked ml-2" style="font-size: 2rem"
              v-text="String(Math.floor(updateAt / 60)).padStart(2, '0') + ':' + String(updateAt % 60).padStart(2, '0')"></span>
          </div>
        </template>

        <template v-slot:text>
          <div class="pr-3 pl-3">
            <v-slider v-model="updateAt" color="primary" track-color="grey" min="0" max="1425" :step="15">
            </v-slider>
          </div>
        </template>

      </v-alert>

      <v-alert variant="default" class="px-1 py-0">
        <template v-slot:title>
          <div class="px-2">
            <span><v-icon color="secondary" style="vertical-align: text-bottom;">mdi-library</v-icon> Songs count</span>
            <span class="time-picked ml-2" style="font-size: 2rem" v-text="songsCount"></span>
          </div>
        </template>

        <template v-slot:text>
          <div class="pr-3 pl-3">
            <v-slider v-model="songsCount" color="primary" track-color="grey" min="5" max="100" :step="5">
            </v-slider>
          </div>
        </template>

      </v-alert>

      <v-divider class="mb-4"></v-divider>

      <div class="px-2">
        <!-- toggle smash button -->

      </div>

      <div v-if="smashEnabled" class="mx-auto pb-3">
        <!-- <div class="mx-auto d-flex justify-space-between"> -->
        <v-btn prepend-icon="mdi-spotify" class="mx-2" color="green-darken-2">Open</v-btn>

        <v-btn prepend-icon="mdi-state-machine" class="mx-2" color="blue-darken-3">Stats</v-btn>
        <!-- </div> -->
      </div>

      <v-card-actions class="justify-center py-2">
        <v-btn variant="outlined" @click="toggleDailySmash" :color="(smashEnabled ? 'red' : 'green') + '-darken-3'"
          class="ma-2">
          <span>{{ smashEnabled ? 'Disable' : 'Enable' }} Daily Smash</span>
        </v-btn>
      </v-card-actions>
    </span>
    <span v-else-if="state === 'loading'">

      <!-- giphy -->
      <v-img style="height:30vh; object-fit: contain" src="https://i.giphy.com/4EALRFjyD5odO.webp">
        <template v-slot:placeholder>
          <div class="d-flex align-center justify-center fill-height">
            <v-progress-circular color="grey-lighten-4" indeterminate></v-progress-circular>
          </div>
        </template>
      </v-img>
      <div class="loading-text">{{ loadingText }}</div>
      <v-card-actions>
      </v-card-actions>
    </span>
    <span v-else-if="state === 'done'">
      <div class="done mt-5">🎉 Daily Smash created!</div>
      <div class="note mb-4">This playlist will now be updated daily!</div>
      <v-tooltip :text="playlistName" location="top">
        <template v-slot:activator="{ props }">
          <code class="playlist-name py-1" v-bind="props">{{ playlistName }}</code>
        </template>
      </v-tooltip>

      <v-card-actions class="justify-center flex-wrap">
        <v-btn color="yellow-darken-4" variant="outlined" class="ma-2" @click="state = 'idle'">Back
        </v-btn>
        <v-btn color="green" variant="outlined" prepend-icon="mdi-spotify" class="ma-2" @click="openPlaylist">
          Open Playlist
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
import shared from '../../shared.js';

export default {
  created() {
    this.request = shared.request.bind(this);
  },

  data() {
    return {
      updateAt: 7 * 60,
      songsCount: 50,

      smashEnabled: false,

      isPlaying: false,

      topicFocus: false,
      direction: 'ltr',
      topicValue: "",

      state: 'idle',  // idle, loading, done, error
      loadingText: 'Applying changes...',

      playlistName: '',
      playlistId: '',
    };
  },

  methods: {
    toggleDailySmash() {
      this.smashEnabled = !this.smashEnabled;
      console.log(this.smashEnabled)
      this.state = 'loading';

      console.log(this.state)

      this.request('/api/daily-smash', this.onDailySmash, (err) => {
        console.log(err);
      }, {
        method: 'POST',
        body: JSON.stringify({
          enabled: this.smashEnabled,
          update_at: this.updateAt,
          songs_count: this.songsCount,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        })
      });
    },


    openPlaylist() {
      window.open(`spotify:user:spotify:playlist:${this.playlistId}`, '_blank')
    },
    generatePlaylist() {
      // make sure the user entered a topic
      const e = document.getElementById("topic-input");
      const topic = e.value;

      if (!topic)
        return e.focus();


      const songsCount = this.songsCount;
      console.log(topic, songsCount)

      this.state = 'loading';

      const loadingMessages = [
        'Landing on the moon...',
        'Fighting sharks...',
        'Drinking a coffee...',
        'Finishing homework...',
        'Playing the guitar...',
        'Reading shakespeare...',
        'Eating a pizza...',
        'Checking the weather...',
        'Fixing the engine...',
        'Fueling the rocket...',
        'Taking a shower...',
        'Walking the dog...',
        'Doing the dishes...',
        'Taking a nap...',
        'Doing the laundry...',
      ]

      this.writeLoadingMessages(loadingMessages);

      // generate the playlist

      this.request('/api/generate-playlist', this.onPlaylistGenerated, (err) => {
        console.log(err);
      }, {
        method: 'POST',
        body: JSON.stringify({
          topic: topic,
          songs_count: songsCount,
          timezone_offset: new Date().getTimezoneOffset()
        })
      });

    },

    onDailySmash(js) {
      if (js.error || js.detail) {
        this.state = 'error';

        if (js.detail)
          this.error = js.detail.map(d => `(${d.loc[1]}) ${d.msg}`).join('\n');
        else
          this.error = js.error;
        return;
      }

      this.smashEnabled = js.enabled;

      if (js.playlist_id) {
        const pid = js.playlist_id;

        this.playlistId = pid;
        this.playlistName = js.playlist_name;
        this.state = 'done';
        this.loadingText = '';
      } else {
        this.state = 'idle';
      }

    },

    async sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },
    array_pick(array) {
      return array[Math.floor(Math.random() * array.length)];
    },

    async writeLoadingMessages(messages) {
      var playedMsgs = [];
      this.loadingText = ''
      while (this.state === 'loading') {
        let msg = this.array_pick(messages);
        if (playedMsgs.includes(msg))
          continue;


        for (let j = 0; j < msg.length; j++) {
          this.loadingText += msg[j];
          if (this.state !== 'loading') return
          await this.sleep(120);
        }

        if (this.state !== 'loading') return
        await this.sleep(1000)
        this.loadingText = ''

      }

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
