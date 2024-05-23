<template>
  <header>
    <div v-if="appOffline">
      <span class="app-offline">
        <h3>Looks like we are down atm 💔</h3>
      </span>
    </div>

    <div class="not-logged" v-else-if="logged === false">
      <div class="note">
        To start using <span muzee>Muzee</span>, please log in with your Spotify account.
      </div>

      <v-btn size="x-large" prepend-icon="mdi-spotify" class="mt-3" color="pink" @click="connectSpotify()"
        :disabled="disableAll">
        Connect Spotify
      </v-btn>
    </div>

    <!-- loading -->
    <div class="profile-loading" v-else-if="(logged === null) || (logged && !id)">
      <v-skeleton-loader class="mx-auto" elevation="12" max-width="300" type="avatar, text"></v-skeleton-loader>
    </div>

    <!-- logged -->
    <div class="logged" v-else>
      <div class="profile">
        <v-avatar :image="photo" size="50"></v-avatar>
        <span class="username ml-2">{{ username }}</span>
      </div>
      <div class="actions mt-2">
        <v-btn color="blue-darken-4">Dashboard</v-btn>
        <v-btn class="ml-3" color="red-darken-4" @click="tryToLogout">Log Out</v-btn>
      </div>
    </div>
  </header>



  <v-divider class="my-5"></v-divider>

  <v-row align="center" justify="center">
    <v-col cols="auto" v-for="feat in features" :tabindex="0" class="card" :enabled="enabledFeatures.includes(feat.key)"
      :is-activation="feat.isActivation" :is-logged="logged" @click="featureCardClick(feat.key)"
      @keydown="k => k.key === 'Enter' && featureCardClick(feat.key)">
      <v-card class="mx-auto feature-card" max-width="344" :disabled="feat.wip || disableAll || appOffline"
        :wip="feat.wip">
        <template v-slot:title>
          {{ feat.title }}

          <span class="status-chip" v-if="logged">
            <v-chip color="purple" variant="text" v-if="!feat.isActivation">run</v-chip>
            <v-chip color="light-green" variant="text" v-else-if="enabledFeatures.includes(feat.key)">enabled</v-chip>
            <v-chip color="orange" variant="text" v-else>activate</v-chip>
          </span>

        </template>
        <template v-slot:subtitle>
          <v-icon>{{ feat.subtitleIcon }}</v-icon>
          {{ feat.subtitle }}
        </template>
        <v-card-text v-html="feat.text"></v-card-text>
      </v-card>
    </v-col>

  </v-row>

  <!-- dialog for an opened feature -->
  <!--     <DailySmash/>
    <PlaylistGenerator/>
    <LanguageFilter/>
    <PublicLiked/>
    <LiveWeather/>
    <LikedArchive/> -->

  <v-dialog :persistent="componentLoading" v-model="featureDialog" min-width="30%" width="auto" v-if="currentFeature"
    class="mx-auto">
    <v-card style="font-family: 'Bree Serif'">
      <template v-slot:title>
        <div class="d-flex justify-space-between">
          <span>
            {{ currentFeature?.title }}
            <v-chip v-if="currentFeature.isActivation" size="small"
              :color="enabledFeatures.includes(currentFeature.key) ? 'green' : 'red'">{{
      enabledFeatures.includes(currentFeature.key) ? 'ON' : 'OFF' }}</v-chip>
          </span>

          <span class="status-chip">
            <v-chip color="red" variant="text" :disabled="componentLoading"
              @click="featureDialog = false">Close</v-chip>
          </span>
        </div>

      </template>

      <template v-slot:subtitle>
        <v-icon>{{ currentFeature.subtitleIcon }}</v-icon>
        {{ currentFeature.short }}
      </template>

      <v-card-text>
        <div class="my-5">
          <component :feature="currentFeature" :enabledFeatures="enabledFeatures" :is="currentFeature?.component"
            id="feature-component" @start-loading="componentStartLoading()" @stop-loading="componentStopLoading()"
            @display-error="componentDisplayError" @feature-toggle="componentFeatureToggle" @show-toast="showSnackbar">
          </component>
          <div id="component-loading" style="display: none;">
            <v-img style="border-radius:10px;height:20vh; object-fit: contain"
              src="https://i.giphy.com/4EALRFjyD5odO.webp">
              <template v-slot:placeholder>
                <div class="d-flex align-center justify-center fill-height">
                  <v-progress-circular color="grey-lighten-4" indeterminate></v-progress-circular>
                </div>
              </template>
            </v-img>
            <div class="text-center">
              <span class="loading-icon" :rot="loadingIcon">⏳</span>
              {{ loadingText }}
            </div>
          </div>
          <div id="component-error" style="display: none !important"
            class="d-flex justify-center align-center flex-column">
            <v-alert icon="mdi-alert-circle" variant="tonal" color="red-darken-3">
              {{ displayError }}
            </v-alert>
            <v-btn color="red-darken-3" variant="outlined" prepend-icon="mdi-repeat" class="mt-5"
              @click="componentTryAgain()">
              Try again
            </v-btn>
          </div>



        </div>
      </v-card-text>
    </v-card>
  </v-dialog>


  <v-footer class="d-flex flex-column" id="footer" v-if="dtApiStatus">
    <div>
      Current State: <v-chip class="status-chip">{{ logged ? 'logged in' : 'not logged' }}</v-chip> |
      Users Served: <v-chip class="status-chip">{{ dtServedUsers || '0' }}</v-chip> |
      API Status: <v-chip class="status-chip">{{ dtApiStatus || 'offline' }}</v-chip>
    </div>
  </v-footer>

  <v-dialog v-model="logoutDialog" width="auto" persistent>
    <v-card class="text-center">
      <v-card-title>
        Are you sure?
      </v-card-title>
      <v-card-text>
        By logging out, the following services will stop working:
        <div class="mt-3"></div>
        <v-chip v-for="feat of enabledFeatures" :key="feat" color="red">
          {{ features.find(f => f.key === feat).title }}
        </v-chip>
        <v-divider class="mt-3"></v-divider>

        <v-switch :model-value="true" color="red-darken-3" class="my-0 py-0" hide-details
          @change="logoutDeleteData = !logoutDeleteData" :style="{ 'color': logoutDeleteData ? '#ff4757' : '#2ed573' }">
          <template v-slot:label>Forget settings? ({{ logoutDeleteData ? 'yes' : 'no' }})</template>
        </v-switch>

      </v-card-text>
      <v-card-actions class="justify-center">
        <v-btn color="green-darken-1" variant="outlined"
          @click="logoutDialog = false; logoutDeleteData = true;">Nevermind</v-btn>
        <v-btn color="red-darken-1" variant="outlined" @click="logoutDialog = false; doLogout()"><b>Log Out</b></v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-snackbar v-model="alertSnackbar" color="red-darken-2" :timeout="1500">
    {{ alertSnackbarMessage }}
    <template v-slot:actions>
      <v-btn color="grey-lighten-2" variant="text" @click="alertSnackbar = false">
        Close
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script>


import DailySmash from '@/components/features/DailySmash.vue';
import PlaylistGenerator from '@/components/features/PlaylistGenerator.vue';
import LanguageFilter from '@/components/features/LanguageFilter.vue';
import PublicLiked from '@/components/features/PublicLiked.vue';
import LiveWeather from '@/components/features/LiveWeather.vue';

export default {
  components: {
    DailySmash,
    PlaylistGenerator,
    LanguageFilter,
    PublicLiked,
    LiveWeather,
  },

  created() {
    this.request = shared.request.bind(this);
  },

  data() {


    return {
      featureDialog: true,
      currentFeature: null,
      currentFeatureName: null,
      componentLoading: false,
      loadingText: '',
      loadingIcon: 'l',
      displayError: '',

      // snackbar
      alertSnackbar: false,
      alertSnackbarMessage: "🚀",

      // debugging

      // server status
      appOffline: false,
      dtServedUsers: null,
      dtApiStatus: null,

      // app
      auth: null,

      // spotify state
      logged: false,
      id: null, //'69420',
      username: null, //'Niryo',
      photo: null, //'https://i.scdn.co/image/ab6775700000ee85c796fdb5cfcad86fbb2e3e7d',


      // ui
      logoutDialog: false,
      logoutDeleteData: true,
      disableAll: false,

      features: [
        {
          key: 'daily-smash',
          isActivation: true,
          title: '🪩 Daily Smash',
          subtitle: 'dynamic playlist',
          subtitleIcon: 'mdi-calendar-clock-outline',
          text: 'Your <u>Daily Smash</u> playlist will refresh daily with songs taken from your library.',
          short: 'Configure your daily playlist',
          wip: false,
          component: 'DailySmash',
        },
        {
          key: 'playlist-generator',
          title: '🎲 Playlist Generator',
          subtitle: 'new playlist',
          subtitleIcon: 'mdi-cube-send',
          text: 'Provide one or more topics and let the <u>Playlist Generator</u> suprise you with a new playlist.',
          short: "Create a playlist based on a topic",
          component: 'PlaylistGenerator',
        },
        {
          key: 'language-filter',
          title: '🙊 Language Filter',
          subtitle: 'playlist editor',
          subtitleIcon: 'mdi-playlist-edit',
          text: 'You don\'t have to skip all the time, just choose a playlist and filter the songs in it by language.',
          short: "Filter songs by language",
          component: 'LanguageFilter',
        },
        {
          key: 'public-liked',
          isActivation: true,
          title: '🩷 Public Liked',
          subtitle: 'dynamic playlist',
          subtitleIcon: 'mdi-calendar-clock-outline',
          text: 'Automatically mirror your liked songs playlist to a public playlist that you can share.',
          short: 'Share your liked songs',
          component: 'PublicLiked'
        },
        {
          key: 'live-weather',
          isActivation: true,
          title: '🌦️ Live Weather',
          subtitle: 'description editor',
          subtitleIcon: 'mdi-text',
          text: 'Have your playlist description live updated with the current weather.',
          short: 'Live weather in your playlist',
          component: 'LiveWeather'
        },
        {
          key: 'liked-archive',
          isActivation: true,
          title: '📦 Liked Archive',
          subtitle: 'dynamic playlist',
          subtitleIcon: 'mdi-calendar-clock-outline',
          text: 'Saves songs that you first liked and then discarded to a playlist that you can check later.',
          wip: true
        }
      ],

      // app
      enabledFeatures: []
    }
  },

  created() {
    // has auth param? (after oauth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const paramToken = urlParams.get('token');

    if (paramToken) {
      localStorage.setItem(this.api.tokenName, paramToken);
      window.history.replaceState(null, '', window.location.pathname);
    }
  },


  async mounted() {
    this.logged = localStorage.getItem(this.api.tokenName) ? true : false;

    console.log(`Logged: ${this.logged}`)

    const js = await this.api.status();

    if (js.error === "network") {
      this.appOffline = true;
      this.dtApiStatus = 'offline';
      return
    }

    this.dtServedUsers = js.served_users;
    this.dtApiStatus = js.status;
    this.logged = js.is_logged;

    if (this.logged) {
      const profile = js.profile;
      this.id = profile.id;
      this.username = profile.username;
      this.photo = profile.photo;

      this.enabledFeatures = js.enabled_features || [];
    }



    // [debug] logged / not logged state
    // const that = this;
    // setInterval(() => {
    //   that.logged = !that.logged;
    // }, 2000)
  },
  methods: {
    toggleComponentView(show) {
      const ids = ["component-loading", "feature-component", "component-error"];

      ids.forEach(id => {
        document.querySelector(`#${id}`).setAttribute("style", `${id === show ? 'display: block;' : 'display: none !important;'}`);
      })
    },

    componentStartLoading() {
      console.log("start")
      this.toggleComponentView("component-loading");
      this.componentLoading = true;

      this.writeLoadingMessages([
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

      )
    },

    componentStopLoading() {
      console.log("stop")
      this.toggleComponentView("feature-component");
      this.componentLoading = false;
    },

    componentDisplayError(error) {
      this.toggleComponentView("component-error");

      if (error.type === "ValidationError") {
        error = error.detail.map(d => `${d.loc[0].charAt(0).toUpperCase() + d.loc[0].slice(1)} ${d.msg.charAt(0).toLowerCase() + d.msg.slice(1)}`).join('\n');
      }

      this.displayError = error;
    },

    componentTryAgain() {
      this.toggleComponentView("feature-component");
    },

    componentFeatureToggle(key, enabled) {
      console.log("TOGGLEED!")
      if (enabled) {
        this.enabledFeatures.push(key);
      } else {
        this.enabledFeatures = this.enabledFeatures.filter(f => f !== key);
      }
      console.log(this.enabledFeatures)
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
      while (this.componentLoading) {
        let msg = this.array_pick(messages);
        if (playedMsgs.includes(msg))
          continue;


        for (let j = 0; j < msg.length; j++) {
          this.loadingText += msg[j];
          this.loadingIcon = this.loadingIcon == 'l' ? 'r' : 'l';
          if (!this.componentLoading) return
          await this.sleep(120);
        }

        if (!this.componentLoading) return
        await this.sleep(1000)
        this.loadingText = ''

      }

    },



    async connectSpotify(after_path) {
      if (after_path) localStorage.setItem("after_path", after_path);
      else {
        console.log('removing since none', after_path)
        localStorage.removeItem("after_path");
      }

      await this.api.redirectToLogin();
      this.disableAll = true;
    },

    tryToLogout() {
      if (this.enabledFeatures?.length > 0)
        this.logoutDialog = true;
      else
        this.doLogout();
    },

    doLogout() {
      localStorage.setItem(this.api.tokenName, '');
      this.logged = false;
      // await this.api.logout({ delete_data: this.logoutDeleteData });
    },

    featureCardClick(key) {
      if (this.appOffline) return;
      if (this.features.find(f => f.key === key).wip) return;

      if (!this.logged) {
        return this.connectSpotify(key);
      };

      this.currentFeature = this.features.find(f => f.key === key);
      this.featureDialog = true;
    },
    // Snackbar
    showSnackbar(message) {
      this.alertSnackbarMessage = message;
      this.alertSnackbar = true;
    },

  }
}
</script>

<style>
.loading-icon {
  /* rotate animation */
  display: inline-block;
  animation: spin 1s infinite linear;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(180deg);
  }
}

.loading-icon[rot="l"] {
  /* 90deg rot */
  /* transform: rotate(90deg) !important; */
  display: inline-block;
  /* transition: .3s; */
}

.loading-icon[rot="r"] {
  /* 90deg rot */
  /* transform: rotate(0deg) !important; */
  display: inline-block;
  /* transition: .3s; */
}

.card[enabled="false"][is-activation="true"][is-logged="true"]> {
  opacity: .5;
}

.feature-card {
  cursor: pointer;
  border-radius: 15px !important;
}

.feature-card:hover {
  transition: .1s;
  /* transform: scale(1.01); */
  filter: drop-shadow(0 0 .5rem #df5fede6) brightness(1.1);
}

.v-dialog {
  /* transition: .1s; */
  /* transform: scale(1.01); */
  filter: drop-shadow(0 0 .5rem #df5fede6) brightness(1.1);
}

.username {
  color: #FDA7DF;

  font-weight: 500;
  font-size: 2rem;
  /* shadow */
  text-shadow: 0 0 1px #df5fede6, 0 0 2px #df5fede6, 0 0 3px #df5fede6, 0 0 4px #df5fede6;

  /* same line as image to the left */
  vertical-align: middle;
}

.app-offline {
  text-shadow: 0px 3px 20px black;
  color: #707071;
}

[wip="true"] {
  opacity: .5 !important;
}


[wip="true"]::before {
  content: "";
  position: absolute;
  top: 0;
  left: -43px;
  width: 100%;
  z-index: 9;
  height: 100%;
  background: url('https://www.seekpng.com/png/full/516-5160620_work-in-progress-configuration-file.png') center center / cover no-repeat;
}
</style>

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

.v-slider-thumb__label {
  color: #eee !important;
  background-color: #AB47BC !important;
}

.v-slider-thumb__label::before {
  color: #AB47BC !important;
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

.time-picked {
  font-weight: bold;
  color: #d27de0;
}
</style>