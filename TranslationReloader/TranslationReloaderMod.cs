using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Config;

namespace TranslationReloader
{
    public class TranslationReloaderMod : ModSystem
    {
        public override double ExecuteOrder() => double.MaxValue;

        public override void Start(ICoreAPI api)
        {
            base.Start(api);
            api.Logger.Notification("[Belarusian Translations Pack] Initialized (ExecuteOrder: {0})", double.MaxValue);
        }

        public override void AssetsLoaded(ICoreAPI api)
        {
            base.AssetsLoaded(api);

            try
            {
                // Find translation pack Origin
                IAssetOrigin? packOrigin = null;
                foreach (var origin in api.Assets.Origins)
                {
                    if (origin.OriginPath.Contains("belarusiantranslationspack", StringComparison.OrdinalIgnoreCase))
                    {
                        packOrigin = origin;
                        break;
                    }
                }

                if (packOrigin == null)
                {
                    api.Logger.Warning("[Belarusian Translations Pack] Cannot find translation pack Origin!");
                    return;
                }

                // Get Origins list via reflection
                var originsField = api.Assets.GetType().GetField("Origins",
                    System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance);

                if (originsField == null)
                {
                    api.Logger.Error("[Belarusian Translations Pack] Cannot access Origins field");
                    return;
                }

                var origins = originsField.GetValue(api.Assets) as List<IAssetOrigin>;
                if (origins == null)
                {
                    api.Logger.Error("[Belarusian Translations Pack] Origins is not List<IAssetOrigin>");
                    return;
                }

                // Move translation pack Origin to the end
                var currentIndex = origins.IndexOf(packOrigin);
                if (currentIndex < 0) return;

                origins.RemoveAt(currentIndex);
                origins.Add(packOrigin);

                api.Logger.Notification("[Belarusian Translations Pack] Moved Origin from position {0} to {1} (last)", currentIndex, origins.Count - 1);

                // Reload translations
                if (Lang.AvailableLanguages.TryGetValue(Lang.CurrentLocale, out var translationService))
                {
                    translationService.Invalidate();
                    Lang.Load(api.Logger, api.Assets, Lang.CurrentLocale);
                    api.Logger.Notification("[Belarusian Translations Pack] ✓ Translations reloaded!");
                }
            }
            catch (Exception ex)
            {
                api.Logger.Error("[Belarusian Translations Pack] Failed: {0}", ex.Message);
            }
        }
    }
}
