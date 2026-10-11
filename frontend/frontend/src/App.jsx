import { useState } from "react";
import { Canvas } from "@react-three/fiber";
import {
  OrbitControls,
  Environment,
  Center,
  useGLTF,
} from "@react-three/drei";

import "./App.css";


function Model({ url }) {
  const { scene } = useGLTF(url);

  return (
    <Center>
      <primitive object={scene} scale={1.8} />
    </Center>
  );
}


function Viewer({ modelUrl }) {

  if (!modelUrl) {
    return (
      <div className="viewer-placeholder">
        <div className="model-placeholder">◇</div>

        <h3>Your model will appear here</h3>

        <p>
          Enter a prompt and generate your first 3D asset.
        </p>
      </div>
    );
  }

  return (
    <Canvas camera={{ position: [3, 2, 5], fov: 45 }}>

      <ambientLight intensity={1.5} />

      <directionalLight
        position={[5, 5, 5]}
        intensity={3}
      />

      <Environment preset="studio" />

      <Model url={modelUrl} />

      <OrbitControls
        enableDamping
        autoRotate
        autoRotateSpeed={1.5}
      />

    </Canvas>
  );
}


function App() {

  const [prompt, setPrompt] = useState("");

  const [loading, setLoading] = useState(false);

  const [modelUrl, setModelUrl] = useState(null);

  const [previewUrl, setPreviewUrl] = useState(null);

  const [error, setError] = useState("");


  const generateModel = async () => {

    if (!prompt.trim()) {
      setError("Please enter a description.");
      return;
    }

    setLoading(true);
    setError("");
    setModelUrl(null);
    setPreviewUrl(null);

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/generate",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            prompt: prompt.trim(),
          }),
        }
      );


      const data = await response.json();


      if (!response.ok) {

        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail)
        );
      }


      if (!data.model_url) {

        throw new Error(
          "No 3D model URL was returned."
        );
      }


      setModelUrl(data.model_url);

      setPreviewUrl(data.preview_url || null);

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Unable to generate the model."
      );

    } finally {

      setLoading(false);
    }
  };


  const downloadModel = () => {

    if (!modelUrl) return;

    const link = document.createElement("a");

    link.href = modelUrl;

    link.download = "polygen-model.glb";

    link.target = "_blank";

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
  };


  return (

    <div className="app">

      <header className="header">

        <div className="logo">

          <span className="logo-symbol">
            ◇
          </span>

          <span>
            PolyGen
          </span>

        </div>

        <div className="tagline">
          AI Text-to-3D Asset Generator
        </div>

      </header>


      <main className="container">

        <section className="hero">

          <h1>
            Turn your ideas into
            <span> 3D assets.</span>
          </h1>

          <p>
            Describe an object and generate
            a textured 3D model.
          </p>

        </section>


        <section className="generator">

          <div className="prompt-card">

            <h2>
              Describe your object
            </h2>

            <p className="hint">
              Tell PolyGen what you want to create.
            </p>

            <textarea
              value={prompt}
              onChange={(event) =>
                setPrompt(event.target.value)
              }
              placeholder="Example: A rusted medieval sword with a glowing blue sapphire..."
              disabled={loading}
            />


            <button
              className="generate-button"
              onClick={generateModel}
              disabled={loading}
            >

              {loading
                ? "Generating 3D Model..."
                : "✨ Generate 3D Model"}

            </button>


            {error && (

              <div className="error-message">
                ⚠️ {error}
              </div>

            )}


            {modelUrl && (

              <button
                className="download-button"
                onClick={downloadModel}
              >
                ⬇ Download GLB
              </button>

            )}

          </div>


          <div className="viewer-card">

            <div className="viewer-header">

              <h2>
                3D Preview
              </h2>

              <span className="status">

                <span className="status-dot"></span>

                {loading
                  ? "Generating"
                  : modelUrl
                    ? "Generated"
                    : "Ready"}

              </span>

            </div>


            <div className="viewer">

              {loading ? (

                <div className="loading-model">

                  <div className="loading-ring"></div>

                  <h3>
                    Creating your 3D model...
                  </h3>

                  <p>
                    This may take a little while.
                  </p>

                </div>

              ) : (

                <Viewer modelUrl={modelUrl} />

              )}

            </div>

          </div>

        </section>


        {previewUrl && (

          <section className="preview-section">

            <h2>
              Generated Preview
            </h2>

            <img
              src={previewUrl}
              alt="Generated 3D model preview"
              className="preview-image"
            />

          </section>

        )}


        <section className="features">

          <div className="feature">

            <div className="feature-icon">
              🧠
            </div>

            <h3>
              AI Generation
            </h3>

            <p>
              Generate 3D models from
              natural language prompts.
            </p>

          </div>


          <div className="feature">

            <div className="feature-icon">
              🎨
            </div>

            <h3>
              Textured Models
            </h3>

            <p>
              Generate textured PBR 3D assets.
            </p>

          </div>


          <div className="feature">

            <div className="feature-icon">
              ⚡
            </div>

            <h3>
              Mesh Optimization
            </h3>

            <p>
              Control polygon count for
              efficient models.
            </p>

          </div>


          <div className="feature">

            <div className="feature-icon">
              📦
            </div>

            <h3>
              GLB Export
            </h3>

            <p>
              Download your model as a GLB asset.
            </p>

          </div>

        </section>

      </main>


      <footer>
        PolyGen • Generative 3D AI
      </footer>

    </div>
  );
}


export default App;