>Dual-Screen Shell with Per-Tab
# External Content

```cpp
using System;
using UIKit;
using Xamarin.Forms;
using Xamarin.Forms.Platform.iOS;
using YourApp;
using YourApp.iOS.Renderers;

[assembly: ExportRenderer(typeof(AppShell), typeof(PerTabDualScreenRenderer))]
namespace YourApp.iOS.Renderers
{
    public class PerTabDualScreenTabBarTracker : ShellTabBarAppearanceTracker
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
        public void UpdateTabBar(float scrollOffset, UITabBarController controller)
        {
            if (blurView != null)
            {
                var alpha = Math.Min(1f, Math.Max(0.3f, 1 - scrollOffset));
                blurView.Alpha = alpha;
                controller.TabBar.BarTintColor = UIColor.White.ColorWithAlpha(alpha);
            }
        }
    }
    public class PerTabDualScreenRenderer : ShellRenderer
    {
        PerTabDualScreenTabBarTracker tracker;
        UIWindow externalWindow;
        UIViewController[] externalPages;
        protected override IShellTabBarAppearanceTracker CreateTabBarAppearanceTracker()
        {
            tracker = new PerTabDualScreenTabBarTracker();
            return tracker;
        }
        public PerTabDualScreenRenderer()
        {
            UIScreen.DidConnectNotification += ScreenDidConnect;
            UIScreen.DidDisconnectNotification += ScreenDidDisconnect;
        }
        // Setup external display
        private void ScreenDidConnect(NSNotification notification)
        {
            var screen = notification.Object as UIScreen;
            if (screen == null) return;
            externalWindow = new UIWindow(screen.Bounds)
            {
                Screen = screen,
                RootViewController = new UIViewController()
            };
            // Create per-tab content for external screen
            externalPages = new UIViewController[]
            {
                new UIViewController { View = CreateExternalLabel("Tab 1 External") },
                new UIViewController { View = CreateExternalLabel("Tab 2 External") },
                new UIViewController { View = CreateExternalLabel("Tab 3 External") }
            };
            // Show the first tab by default
            externalWindow.RootViewController = externalPages[0];
            externalWindow.Hidden = false;
        }
        private UIView CreateExternalLabel(string text)
        {
            var label = new UILabel
            {
                Text = text,
                TextColor = UIColor.White,
                TextAlignment = UITextAlignment.Center,
                Frame = UIScreen.MainScreen.Bounds
            };
            var view = new UIView();
            view.BackgroundColor = UIColor.Black;
            view.AddSubview(label);
            return view;
        }
        private void ScreenDidDisconnect(NSNotification notification)
        {
            if (externalWindow != null)
            {
                externalWindow.Hidden = true;
                externalWindow.Dispose();
                externalWindow = null;
            }
        }
    // Update main tab bar blur
        public void OnScroll(float scrollOffset)
        {
            tracker?.UpdateTabBar(scrollOffset, TabBarController);
        }
        // Switch external content per selected tab
        public void SwitchExternalTab(int index)
        {
            if (externalWindow != null && externalPages != null && index >= 0 && index < externalPages.Length)
            {
                externalWindow.RootViewController = externalPages[index];
            }
        }
    }
}
```
⸻

How It Works
	1.	External Display Detection:
Listens for UIScreen.DidConnectNotification and DidDisconnectNotification.
	2.	Per-Tab External Pages:
	•	externalPages array holds a separate UIViewController for each tab.
	•	You can customize each page with metrics, charts, videos, or custom controls.
	3.	Switch External Content:
	•	Call SwitchExternalTab(index) whenever the main Shell tab changes.
	•	The external display updates to match the selected tab’s content or show entirely different content.
	4.	Dynamic Blur on Main Tab Bar:
	•	Still supports glass/frosted tab bar with dynamic transparency on the main screen.

⸻

Usage Example
```cpp
// When tab changes
Shell.Current.CurrentItemChanged += (s, e) =>
{
    var renderer = (PerTabDualScreenRenderer)Shell.Current.GetRenderer();
    renderer?.SwitchExternalTab(Shell.Current.CurrentItem.Stack.IndexOf(Shell.Current.CurrentItem.CurrentItem));
};

// Scroll effect
void OnScrollChanged(object sender, ScrolledEventArgs e)
{
    var scrollOffset = (float)Math.Min(1.0, e.ScrollY / 200);
    var renderer = (PerTabDualScreenRenderer)Shell.Current.GetRenderer();
    renderer?.OnScroll(scrollOffset);
}


⸻
