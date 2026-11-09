import unittest
import ai_service


class TestImageGeneration(unittest.TestCase):
    def test_is_image_request(self):
        self.assertTrue(ai_service.is_image_request("/image a futuristic cybernetic tiger"))
        self.assertTrue(ai_service.is_image_request("/imagine sunset on Mars"))
        self.assertTrue(ai_service.is_image_request("/draw a cute puppy"))
        self.assertTrue(ai_service.is_image_request("/paint a starry night"))
        self.assertTrue(ai_service.is_image_request("generate an image of a red Ferrari"))
        self.assertTrue(ai_service.is_image_request("create a picture of an enchanted forest"))
        self.assertTrue(ai_service.is_image_request("can you draw an astronaut floating in space?"))
        self.assertTrue(ai_service.is_image_request("draw a serene mountain landscape at sunrise"))
        self.assertTrue(ai_service.is_image_request("show me an image of a cyber city"))

        # Non-image requests should be False
        self.assertFalse(ai_service.is_image_request("what is image processing in Python?"))
        self.assertFalse(ai_service.is_image_request("how to draw a border in CSS"))
        self.assertFalse(ai_service.is_image_request("hello, who made you?"))
        self.assertFalse(ai_service.is_image_request(""))

    def test_extract_image_prompt(self):
        self.assertEqual(
            ai_service.extract_image_prompt("/image a futuristic cybernetic tiger"),
            "a futuristic cybernetic tiger",
        )
        self.assertEqual(
            ai_service.extract_image_prompt("generate an image of a red sports car"),
            "a red sports car",
        )
        self.assertEqual(
            ai_service.extract_image_prompt("can you draw an astronaut in deep space?"),
            "an astronaut in deep space",
        )
        self.assertEqual(
            ai_service.extract_image_prompt("draw a peaceful garden"),
            "a peaceful garden",
        )

    def test_get_flux_image_url(self):
        url = ai_service.get_flux_image_url("a red sports car", seed=42)
        self.assertIn("https://image.pollinations.ai/prompt/", url)
        self.assertIn("model=flux", url)
        self.assertIn("nologo=true", url)
        self.assertIn("seed=42", url)
        self.assertIn("width=1024", url)
        self.assertIn("height=1024", url)

    def test_format_image_markdown(self):
        url = "https://image.pollinations.ai/prompt/cat?model=flux"
        md = ai_service.format_image_markdown("a cyber cat", url)
        self.assertIn("🎨 **Generated AI Image with FLUX.1**", md)
        self.assertIn("![a cyber cat]", md)
        self.assertIn(url, md)
        self.assertIn("Download Full HD Image", md)

    def test_mock_engine_generates_image(self):
        reply = ai_service.MockAIEngine.generate_reply(
            [{"role": "user", "content": "/image neon samurai warrior"}],
            system_prompt="",
        )
        self.assertIn("🎨 **Generated AI Image with FLUX.1**", reply)
        self.assertIn("neon samurai warrior", reply)
        self.assertIn("image.pollinations.ai", reply)


if __name__ == "__main__":
    unittest.main()
