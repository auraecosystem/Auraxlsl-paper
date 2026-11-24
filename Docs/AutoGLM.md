# AutoGLM-Phone-Multilingual

## <Icon icon="rectangle-list" iconType="solid" color="#ffffff" size={36} />   Overview

AutoGLM-Phone-Multilingual is a mobile intelligent assistant framework built on vision-language models. It understands phone screen content in a multimodal manner and helps users complete tasks through automated operations. The system controls devices via ADB (Android Debug Bridge), perceives screens, and generates and executes operation workflows through intelligent planning. Users simply describe their needs in natural language, such as "Open eBay and search for wireless earphones." and AutoGLM-Phone-Multilingual will complete the entire workflow.

<Tip>
  New model launched, free for a limited time!
</Tip>

<CardGroup cols={2}>
  <Card title="Input Modality" icon="arrow-down-right" color="#ffffff">
    Task Instructions
  </Card>

  <Card title="Output Modality" icon="arrow-down-left" color="#ffffff">
    Task Action
  </Card>

  <Card title="Supported Languages" icon="language" color="#ffffff">
    English & Chinese
  </Card>

  <Card title="Supported Hardware Devices" icon="upload" color="#ffffff">
    Android Phone
  </Card>
</CardGroup>

## <Icon icon="list" iconType="solid" color="#ffffff" size={36} />   Usage

<AccordionGroup>
  <Accordion title="Order Food Delivery">
    Place orders for specific products from designated merchants on food delivery platforms, or request to reorder the meal you most recently purchased.
  </Accordion>

  <Accordion title="Product Purchase">
    Place orders on shopping websites or check product reviews.
  </Accordion>

  <Accordion title="Transportation Services">
    Route planning, nearby searches, flight and ticket booking, hotel reservations, and more.
  </Accordion>

  <Accordion title="News & Information">
    Search for news, play songs and videos, and interact through likes, comments, and favorites.
  </Accordion>

  <Accordion title="Housing & Rentals">
    Search for rentals based on location, budget, layout, and other criteria.
  </Accordion>
</AccordionGroup>

## <Icon icon="bars-sort" iconType="solid" color="#ffffff" size={36} />   Resources

* [API Documentation](/api-reference/llm/chat-completion#vision-model): Learn how to call the API.

## <Icon icon="arrow-down-from-line" iconType="solid" color="#ffffff" size={36} />   Introducing AutoGLM-Phone-Multilingual

<Steps>
  <Step title="Model Highlights" titleSize="h3">
    * **Technical Breadth:**  Powered by the AutoGLM multimodal model combined with ADB-based device control, integrating a complete capability stack including visual understanding, task planning, and tool execution.
    * **Commercial Validation:**  Its practicality and stability have been verified across multiple partnerships and testing scenarios.
    * **Application Value:**  Delivers true end-to-end intelligence, enabling a “say it, get it” mobile control experience.
  </Step>

  <Step title="Supported Apps" stepNumber={2} titleSize="h3">
    AutoGLM-Phone-Multilingual supports 50+ mainstream applications:

    | Category                 | Apps                                                                                              |
    | ------------------------ | ------------------------------------------------------------------------------------------------- |
    | Social & Messaging       | X, Tiktok, WhatsApp, Telegram, FacebookMessenger, GoogleChat, Quora, Reddit, Instagram            |
    | Productivity & Office    | Gmail, GoogleCalendar, GoogleDrive, GoogleDocs, GoogleTasks, Joplin                               |
    | Life, Shopping & Finance | Amazon shopping, Temu, Bluecoins, Duolingo, GoogleFit, ebay                                       |
    | Utilities & Media        | GoogleClock, Chrome, GooglePlayStore, GooglePlayBooks, FilesbyGoogle                              |
    | Travel & Navigation      | GoogleMaps, [Booking.com](http://booking.com/), [Trip.com](http://trip.com/), Expedia, OpenTracks |

    To see the full list of supported apps, run the scripts in [github](https://github.com/zai-org/Open-AutoGLM/blob/main/README.md#%E6%94%AF%E6%8C%81%E7%9A%84%E5%BA%94%E7%94%A8) (feel free to give us a star\~)
  </Step>

  <Step title="Available Actions" stepNumber={3} titleSize="h3">
    AutoGLM-Phone-Multilingual can perform the following actions:

    | Action     | Description                             |
    | ---------- | --------------------------------------- |
    | Launch     | Launch an app                           |
    | Tap        | Tap at specified coordinates            |
    | Type       | Input text                              |
    | Swipe      | Swipe the screen                        |
    | Back       | Go back to previous page                |
    | Home       | Return to home screen                   |
    | Long Press | Long press                              |
    | Double Tap | Double tap                              |
    | Wait       | Wait for page to load                   |
    | Take\_over | Request manual takeover (login/captcha) |
  </Step>
</Steps>

## <Icon icon="objects-column" iconType="solid" color="#ffffff" size={36} />    Examples

<Tabs>
  <Tab title="Play a Taylor Swift song for me.">
    <video src="https://cdn.bigmodel.cn/static/autoglm/201642.mp4" controls />
  </Tab>

  <Tab title="Turn your phone volume up to the maximum.">
    <video src="https://cdn.bigmodel.cn/static/autoglm/115754.mp4" controls />
  </Tab>
</Tabs>

## <Icon icon="rectangle-code" iconType="solid" color="#ffffff" size={36} />    Invocation Guide

### **Environment Setup**

#### 1. Python Environment

It is recommended to use **Python 3.10**.

#### 2. ADB (Android Debug Bridge)

* Download the official ADB package and extract it to a custom directory.

[https://developer.android.com/tools/releases/platform-tools?hl=zh-cn](https://developer.android.com/tools/releases/platform-tools?hl=zh-cn)

* Configure environment variables:
  * **MacOS**：`export PATH=${PATH}:~/Downloads/platform-tools`
  * **Windows:**  Refer to third-party tutorials to configure environment variables.
* Verify whether ADB is installed successfully:

```
# adb --version

Android Debug Bridge version 1.0.41
Version 36.0.0-13206524
Installed as /opt/homebrew/bin/adb
Running on Darwin 22.4.0 (arm64)
```

#### 3. **Android Device Configuration**

* Android 7.0+ device or emulator
* Enable Developer Mode: *Settings → About phone → Tap "Build number" 10 times consecutively*
* Enable USB Debugging: *Settings → Developer options → USB debugging*

#### 4. **Install ADB Keyboard**

Download **ADBKeyboard.apk** and install it on the device. After installation, go to *Settings → Input method* and enable **ADB Keyboard**.

[https://github.com/senzhk/ADBKeyBoard/blob/master/ADBKeyboard.apk](https://github.com/senzhk/ADBKeyBoard/blob/master/ADBKeyboard.apk)

### **Deployment Preparation**

#### 1. Clone the Repository

```
git clone https://github.com/zai-org/Open-AutoGLM.git
```

#### 2. Install Dependencies

```
pip install -r requirements.txt
pip install -e .
```

#### 3. Configure ADB Connection

```
# Check connected devices
adb devices
# Output should show your device, e.g.
# List of devices attached
# emulator-5554   device
```

#### 4. Configure Model API

```
python main.py --base-url https://api-inference.modelscope.cn/v1 --model "ZAI/AutoGLM-Phone-9B" --apikey "your-zai-api-key" ""Open Chrome browser"
```


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.z.ai/llms.txt
