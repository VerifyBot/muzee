<template>
  <v-card variant="tonal" max-width="500" width="auto" class="justify-center mx-auto" :loading="state === 'loading'"
    color="purple-lighten-4">
    <span v-if="state === 'idle'">

      <!-- form -->
      <v-card-text class="pb-0">
        <div class="text-medium-emphasis mb-2">
          <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-sim-outline</v-icon>
          Playlist URL / ID
        </div>
        <v-text-field placeholder="https://open.spotify.com/playlist/..." variant="outlined" spellcheck="false"
          v-model="playlistValue">
          <template #append-inner>
            <v-icon @mousedown.stop @click.stop icon="mdi-open-in-new" @click="openLibrary"></v-icon>
          </template>
        </v-text-field>

        <div class="text-medium-emphasis mb-2">
          <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-map-marker</v-icon>
          Lat, Long
        </div>
        <v-text-field placeholder="29.5363451, 34.9417276" variant="outlined" spellcheck="false" v-model="latlongValue">
          <template #append-inner>
            <v-icon @mousedown.stop @click.stop @click="currentLocation" icon="mdi-target"></v-icon>
          </template>
        </v-text-field>


        <div class="text-medium-emphasis mb-2">
          <v-icon color="secondary" style="vertical-align: text-bottom;">mdi-thermometer-auto</v-icon>
          Temperature scale
        </div>
        <v-select label="Select" variant="outlined" v-model="tempScale" :items="['Celcius', 'Fahrenheit', 'Kelvin']">

          <template v-slot:selection="{ item }">
            <v-icon size="small" v-if="tempScale === 'Celcius'">mdi-temperature-celsius</v-icon>
            <v-icon size="small" v-if="tempScale === 'Fahrenheit'">mdi-temperature-fahrenheit</v-icon>
            <v-icon size="small" v-if="tempScale === 'Kelvin'">mdi-temperature-kelvin</v-icon>
            <span class="ml-2">{{ item.title }}</span>
          </template>
        </v-select>
      </v-card-text>

      <!-- feature playlist -->
      <div v-if="featureEnabled" class="mx-auto pb-3">
        <PlaylistCard v-if="playlistId" :newDelay="true" :playlistId="playlistId" />

      </div>

      <!-- actions -->
      <v-card-actions class="justify-center py-2">
        <v-btn variant="text" @click="toggleFeature" :color="(featureEnabled ? 'red' : 'purple-lighten-2')" class="ma-2"
          size="large" :prepend-icon="featureEnabled ? 'mdi-sleep' : 'mdi-lightbulb-on'">
          <span>{{ featureEnabled ? 'Disable' : 'Enable' }} Live Weather</span>
        </v-btn>
      </v-card-actions>

    </span>
  </v-card>
</template>

<script>

export default {
  async mounted() {
    this.featureEnabled = this.enabledFeatures.includes(this.featureKey);

    if (this.featureEnabled) {
      const js = await this.api.featureDetails({ key: this.featureKey });

      this.playlistId = js.playlist;
      this.playlistImage = js.image;

      // form
      this.updateAt = js.update_at;
      this.songsCount = js.songs_count;
    }
  },

  props: ['feature', 'enabledFeatures'],

  data() {
    return {
      // config
      featureKey: 'live-weather',

      // form
      playlistValue: "",
      latlongValue: "",
      tempScale: "Celcius",

      // activation status
      featureEnabled: false,


      // --------------------------------------
      state: 'idle',  // idle, done, error
      playlistName: '',
      playlistId: '',
      playlistImage: ''
    };
  },

  methods: {
    async toggleFeature() {
      this.$emit("start-loading");

      const js = await this.api.toggleLiveWeather({
        enabled: !this.featureEnabled,
        playlist: this.playlistValue,
        latlong: this.latlongValue,
        temp_scale: this.tempScale.toLowerCase(),
      });

      this.$emit("feature-toggle", this.featureKey, !this.featureEnabled)
      this.$emit("stop-loading");

      if (js.error) {
        this.$emit("display-error", js.error);
        return
      }

      this.featureEnabled = !this.featureEnabled;
      this.playlistId = js.playlist;
      this.playlistImage = js.image;
    },

    currentLocation(e) {
      e.preventDefault();
      // on error / no permission show this.$emit("show-toast", "")
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
          this.latlongValue = `${position.coords.latitude}, ${position.coords.longitude}`;
        }, (error) => {
          const m = {
            1: "please allow location access."
          };

          this.$emit("show-toast", m[error.code] || "cannot determine location.");
        });
      } else {
        this.$emit("show-toast", "Geolocation is not supported by this browser.");

      }
    },
    openLibrary() {
      window.open("spotify:library", '_blank')
    },
  },
}

</script>

<style>
.bold-picked {
  font-weight: bold;
  color: #d27ddf;
}
</style>