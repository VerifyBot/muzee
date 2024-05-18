<template>
  <v-card title="Playlist Generator" subtitle="Create a playlist based on a topic" variant="tonal" max-width="500"
    width="auto" class="justify-center mx-auto" :loading="state === 'loading'">
    <span v-if="state === 'idle'">
      <v-card-text class="pb-0">
        <v-text-field v-model="topicValue" :model-value="topicValue" label="Playlist Topic" variant="solo-filled"
          id="topic-input" hint="for multiple topics seperate with a comma." @focus="topicFocus = true"
          @blur="topicFocus = false" :rules="[v => !!v || '']" required @input="detectLanguageDirection"
          :dir="direction"></v-text-field>

        <v-row class="justify-start px-3">
          <v-btn color="pruple-darken-4" v-if="!topicFocus" size="small" @click="randomTopic">Pick for me</v-btn>
          <div v-else style="height:28px; width: 10rem; background: transparent"></div>
        </v-row>

        <v-row class="pt-9">
          <v-col cols="5" class="text-left mr-0 pr-0" style="line-height: 1.8rem;">
            <span class="songs-count-label">songs count</span>
          </v-col>
          <v-col cols="7" class="pl-3 ml-0">
            <v-slider v-model="songsCount" color="pink-darken-3" step="5" show-ticks="always" thumb-label="always" min="5"
              max="100"></v-slider>
          </v-col>
        </v-row>

      </v-card-text>

      <v-card-actions class="justify-center py-2">
        <v-btn variant="tonal" color="pink-lighten-3" size="large" @click="generatePlaylist">🎲 Generate</v-btn>
      </v-card-actions>
    </span>
    <span v-else-if="state === 'loading'">

      <div class="dice" style="font-size: 4rem;">🎲</div>

      <div class="loading-text">{{ loadingText }}</div>
      <v-card-actions>
      </v-card-actions>
    </span>
    <span v-else-if="state === 'done'">
      <div class="done mt-5 mb-2">🎉 Done</div>
      <v-tooltip :text="playlistName" location="top">
        <template v-slot:activator="{ props }">
          <code class="playlist-name py-1" v-bind="props">{{ playlistName }}</code>
        </template>
      </v-tooltip>

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
import shared from '../../shared.js';

export default {
  created() {
    this.request = shared.request.bind(this);
  },

  data() {
    return {
      topicFocus: false,
      direction: 'ltr',
      topicValue: "",
      songsCount: 50,

      state: 'idle',  // idle, loading, done, error
      loadingText: '',

      playlistName: '',
      playlistId: '',
    };
  },

  methods: {
    detectLanguageDirection() {
      const containsHebrew = /[\u0590-\u05FF]/.test(this.topicValue[0]);
      this.direction = containsHebrew ? 'rtl' : 'ltr';
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

    onPlaylistGenerated(js) {
      this.loadingText = '';
      
      if (js.error || js.detail) {
        this.state = 'error';

        if (js.detail)
          this.error = js.detail.map(d => `(${d.loc[1]}) ${d.msg}`).join('\n');
        else
          this.error = js.error;
        return;
      }

      const pid = js.playlist_id;

      this.playlistId = pid;
      this.playlistName = js.playlist_name;

      this.state = 'done';
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

<style>
.feature-title {
  color: #eee;
  text-decoration: underline;

  @media screen and (max-width: 600px) {
    font-size: 10vw !important;
  }
}

.songs-count-label {
  font-size: 1.2rem;
  user-select: none;
}

.v-card-title,
.v-card-subtitle {
  user-select: none;
}



.v-progress-linear__indeterminate {
  background-color: #b24569 !important;
}

/* the dice should shake and rotate 360deg in an anmation */
.dice {
  animation: shake 0.92s cubic-bezier(.36, .07, .19, .97) both infinite;
  transform: translate3d(0, 0, 0);
  backface-visibility: hidden;
  perspective: 1000px;
  font-size: 4rem;
}

@keyframes shake {

  10%,
  90% {
    transform: translate3d(-1px, 0, 0) rotate(0deg);
  }

  20%,
  80% {
    transform: translate3d(2px, 0, 0) rotate(60deg);
  }

  30%,
  50%,
  70% {
    transform: translate3d(-4px, 0, 0) rotate(120deg);
  }

  40%,
  60% {
    transform: translate3d(4px, 0, 0) rotate(180deg);
  }
}

code.playlist-name {
  font-size: 1.2rem;
  color: #eee;
  background-color: #851339;
  padding: 0.5rem;
  border-radius: 0.5rem;
  user-select: all;
  display: inline-block;
  width: 90%;
  white-space: nowrap;
  overflow: hidden !important;
  text-overflow: ellipsis;

  @media screen and (max-width: 600px) {
    font-size: .8rem;
  }
}
</style>