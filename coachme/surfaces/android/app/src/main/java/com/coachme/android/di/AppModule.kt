package com.coachme.android.di

import android.content.Context
import com.coachme.android.data.ReportStore
import com.coachme.android.data.RunStore
import com.coachme.android.data.SettingsStore
import com.coachme.android.llm.DeepSeekClient
import com.coachme.android.llm.ReportTools
import com.coachme.android.pipeline.Ball
import com.coachme.android.pipeline.Pipeline
import com.coachme.android.pipeline.Pose
import com.coachme.android.pipeline.Sampler
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides @Singleton
    fun json(): Json = Json { ignoreUnknownKeys = true; isLenient = true; encodeDefaults = true }

    @Provides @Singleton
    fun http(): OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(180, TimeUnit.SECONDS)
        .writeTimeout(180, TimeUnit.SECONDS)
        .build()

    @Provides @Singleton
    fun settingsStore(@ApplicationContext ctx: Context) = SettingsStore(ctx)

    @Provides @Singleton
    fun reportStore(@ApplicationContext ctx: Context) = ReportStore(ctx)

    @Provides @Singleton
    fun runStore(@ApplicationContext ctx: Context) = RunStore(ctx)

    @Provides @Singleton
    fun client(http: OkHttpClient, json: Json, settings: SettingsStore) = DeepSeekClient(http, json, settings)

    @Provides @Singleton
    fun reportTools(settings: SettingsStore, store: ReportStore, json: Json) = ReportTools(settings, store, json)

    @Provides @Singleton
    fun sampler(@ApplicationContext ctx: Context) = Sampler(ctx)

    @Provides @Singleton
    fun pose(@ApplicationContext ctx: Context) = Pose(ctx)

    @Provides @Singleton
    fun ball(@ApplicationContext ctx: Context) = Ball(ctx)

    @Provides @Singleton
    fun pipeline(
        sampler: Sampler, pose: Pose, ball: Ball, client: DeepSeekClient, tools: ReportTools,
        store: ReportStore, settings: SettingsStore, json: Json, runStore: RunStore,
    ) = Pipeline(sampler, pose, ball, client, tools, store, settings, json, runStore)
}
