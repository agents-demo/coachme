package com.topspinreview.android.di

import android.content.Context
import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.data.SettingsStore
import com.topspinreview.android.llm.DeepSeekClient
import com.topspinreview.android.llm.ReportTools
import com.topspinreview.android.pipeline.Ball
import com.topspinreview.android.pipeline.Pipeline
import com.topspinreview.android.pipeline.Pose
import com.topspinreview.android.pipeline.Sampler
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
        store: ReportStore, settings: SettingsStore, json: Json,
    ) = Pipeline(sampler, pose, ball, client, tools, store, settings, json)
}
