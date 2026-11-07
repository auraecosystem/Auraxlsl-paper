using System;
using UIKit;
using Xamarin.Forms;
using Xamarin.Forms.Platform.iOS;
using YourApp;
using YourApp.iOS.Renderers;

[assembly: ExportRenderer(typeof(AppShell), typeof(DualScreenGlassShellRenderer))]
namespace YourApp.iOS.Renderers
{
    public class DualScreenGlassTabBarTracker : ShellTabBarAppearanceTracker
    {
        UIVisualEffectView blurView;

        public override void SetAppearance(UITabBarController controller, ShellAppearance appearance)
        {
            controller.TabBar.Translucent = true;

            if (blurView == null)
            {
                var blurEffect = UIBlurEffect.FromStyle(UIBlurEffectStyle.Light);
                blurView = new UIVisualEffectView(blurEffect)
                {
                    Frame = controller.TabBar.Bounds,
                    AutoresizingMask = UIViewAutoresizing.FlexibleWidth | UIViewAutoresizing.FlexibleHeight
                };
                controller.TabBar.InsertSubview(blurView, 0);
            }

            controller.TabBar.TintColor = UIColor.SystemBlue;
            controller.TabBar.UnselectedItemTintColor = UIColor.LightGray;
            controller.TabBar.ClipsToBounds = true;

            base.SetAppearance(controller, appearance);
        }

        // Dynamic transparency
        public void UpdateTabBar(float scrollOffset, UITabBarController controller)
        {
            if (blurView != null)
            {
                var alpha = Math.Min(1f, Math.Max(0.3f, 1 - scrollOffset));
                blurView.Alpha = alpha;
                controller.TabBar.BarTintColor = UIColor.White.ColorWithAlpha(alpha);
            }
        }

        // Animate tab selection
        public void AnimateTabSelection(UITabBarController controller, int index)
        {
            if (controller.TabBar.Items != null && index >= 0 && index < controller.TabBar.Items.Length)
            {
                var tabView = controller.TabBar.Subviews[index + 1];
                UIView.Animate(0.2, () => { tabView.Transform = CGAffineTransform.MakeScale(1.2f, 1.2f); },
                    () => { UIView.Animate(0.2, () => { tabView.Transform = CGAffineTransform.MakeScale(1f, 1f); }); });
            }
        }

        // Set badge per tab
        public void SetBadge(UITabBarController controller, int index, string value)
        {
            if (controller.TabBar.Items != null && index >= 0 && index < controller.TabBar.Items.Length)
                controller.TabBar.Items[index].BadgeValue = value;
        }
    }

    public class DualScreenGlassShellRenderer : ShellRenderer
    {
        DualScreenGlassTabBarTracker tracker;
        UIWindow externalWindow;

        protected override IShellTabBarAppearanceTracker CreateTabBarAppearanceTracker()
        {
            tracker = new DualScreenGlassTabBarTracker();
            return tracker;
        }

        public DualScreenGlassShellRenderer()
        {
            UIScreen.DidConnectNotification += ScreenDidConnect;
            UIScreen.DidDisconnectNotification += ScreenDidDisconnect;
        }

        // Handle external screen connection
        private void ScreenDidConnect(NSNotification notification)
        {
            var screen = notification.Object as UIScreen;
            if (screen == null) return;

            externalWindow = new UIWindow(screen.Bounds)
            {
                Screen = screen,
                RootViewController = new UIViewController()
            };

            // You can show the same Shell page or a different ContentPage
            var page = new ContentPage
            {
                BackgroundColor = Color.Black,
                Content = new Label
                {
                    Text = "External Display",
                    TextColor = Color.White,
                    HorizontalOptions = LayoutOptions.Center,
                    VerticalOptions = LayoutOptions.Center
                }
            };

            externalWindow.RootViewController = page.CreateViewController();
            externalWindow.Hidden = false;
        }

        // Handle external screen disconnect
        private void ScreenDidDisconnect(NSNotification notification)
        {
            if (externalWindow != null)
            {
                externalWindow.Hidden = true;
                externalWindow.Dispose();
                externalWindow = null;
            }
        }

        // Public APIs
        public void OnScroll(float scrollOffset)
        {
            tracker?.UpdateTabBar(scrollOffset, TabBarController);
        }

        public void SelectTab(int index)
        {
            tracker?.AnimateTabSelection(TabBarController, index);
        }

        public void SetTabBadge(int index, string value)
        {
            tracker?.SetBadge(TabBarController, index, value);
        }
    }
}
