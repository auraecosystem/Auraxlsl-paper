using System;
using UIKit;
using Xamarin.Forms;
using Xamarin.Forms.Platform.iOS;
using YourApp;
using YourApp.iOS.Renderers;

[assembly: ExportRenderer(typeof(AppShell), typeof(UltimateGlassShellRenderer))]
namespace YourApp.iOS.Renderers
{
    public class UltimateGlassTabBarAppearanceTracker : ShellTabBarAppearanceTracker
    {
        UIVisualEffectView blurView;

        public override void SetAppearance(UITabBarController controller, ShellAppearance appearance)
        {
            controller.TabBar.Translucent = true;

            // Add blur effect if not exists
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

            // Set default colors
            controller.TabBar.TintColor = UIColor.SystemBlue; // Selected
            controller.TabBar.UnselectedItemTintColor = UIColor.LightGray; // Unselected
            controller.TabBar.ClipsToBounds = true;

            base.SetAppearance(controller, appearance);
        }

        // Update tab bar dynamically
        public void UpdateTabBar(float scrollOffset, UITabBarController controller)
        {
            if (blurView != null)
            {
                var alpha = Math.Min(1f, Math.Max(0.3f, 1 - scrollOffset));
                blurView.Alpha = alpha;
                controller.TabBar.BarTintColor = UIColor.White.ColorWithAlpha(alpha);
            }
        }

        // Animate tab selection icon
        public void AnimateTabSelection(UITabBarController controller, int index)
        {
            if (controller.TabBar.Items != null && index >= 0 && index < controller.TabBar.Items.Length)
            {
                var tab = controller.TabBar.Items[index];
                var tabView = controller.TabBar.Subviews[index + 1]; // Subviews[0] = background
                UIView.Animate(0.2, () =>
                {
                    tabView.Transform = CGAffineTransform.MakeScale(1.2f, 1.2f);
                }, () =>
                {
                    UIView.Animate(0.2, () =>
                    {
                        tabView.Transform = CGAffineTransform.MakeScale(1f, 1f);
                    });
                });
            }
        }

        // Set badge on a tab
        public void SetBadge(UITabBarController controller, int index, string value)
        {
            if (controller.TabBar.Items != null && index >= 0 && index < controller.TabBar.Items.Length)
            {
                controller.TabBar.Items[index].BadgeValue = value;
            }
        }
    }

    public class UltimateGlassShellRenderer : ShellRenderer
    {
        UltimateGlassTabBarAppearanceTracker tracker;

        protected override IShellTabBarAppearanceTracker CreateTabBarAppearanceTracker()
        {
            tracker = new UltimateGlassTabBarAppearanceTracker();
            return tracker;
        }

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

void OnScrollChanged(object sender, ScrolledEventArgs e)
{
    var scrollOffset = (float)Math.Min(1.0, e.ScrollY / 200); // normalize 0-1
    var renderer = (UltimateGlassShellRenderer)Shell.Current.GetRenderer();
    renderer?.OnScroll(scrollOffset);
}

// Call when a tab is selected
var renderer = (UltimateGlassShellRenderer)Shell.Current.GetRenderer();
renderer?.SelectTab(1); // Animate second tab

var renderer = (UltimateGlassShellRenderer)Shell.Current.GetRenderer();
renderer?.SetTabBadge(0, "3"); // Badge "3" on first tab
renderer?.SetTabBadge(2, null); // Remove badge from third tab
