// It adds an extra newline after each case 
switch (someString)
{
    case "a":
        return foo;

    case "b":
        return bar;
}


public static string[] GetScriptingBackendCppDefines(string scriptingBackend)
{
    switch (scriptingBackend.ToLowerInvariant())
    {
        case "il2cpp":
            return new[]
            {
                "ENABLE_MONO=0",
                "ENABLE_IL2CPP=1",
                "ENABLE_DOTNET=0",
                "ENABLE_SERIALIZATION_BY_CODEGENERATION=0",
            };

        case "mono":
            return new[]
            {
                "ENABLE_MONO=1",
                "ENABLE_IL2CPP=0",
                "ENABLE_DOTNET=0",
                "ENABLE_SERIALIZATION_BY_CODEGENERATION=0",
            };

        case "dotnet":
            return new[]
            {
                "ENABLE_MONO=0",
                "ENABLE_IL2CPP=0",
                "ENABLE_DOTNET=1",
                "ENABLE_SERIALIZATION_BY_CODEGENERATION=1",
            };
            
        case "none":
            return new[]
            {
                "ENABLE_MONO=0",
                "ENABLE_IL2CPP=0",
                "ENABLE_DOTNET=0",
                "ENABLE_SERIALIZATION_BY_CODEGENERATION=0",
            };
    }

    throw new NotSupportedException("Not supported scripting backend: " + scriptingBackend);
}