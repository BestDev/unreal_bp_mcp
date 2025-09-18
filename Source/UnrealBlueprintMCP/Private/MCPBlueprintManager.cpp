// Copyright Epic Games, Inc. All Rights Reserved.
// MCPBlueprintManager - Implementation of blueprint creation and property modification

#include "MCPBlueprintManager.h"
#include "MCPSettings.h"

// Editor-only includes (wrapped in WITH_EDITOR)
#if WITH_EDITOR
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Blueprint.h"
#include "UObject/Package.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Character.h"
#include "Components/ActorComponent.h"
#include "Blueprint/UserWidget.h"
#include "AssetToolsModule.h"
#include "IAssetTools.h"
#include "PackageTools.h"
#include "FileHelpers.h"
#endif

// JSON includes
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

// Unreal includes
#include "Engine/Engine.h"
#include "Misc/DateTime.h"
#include "Misc/Guid.h"

DEFINE_LOG_CATEGORY_STATIC(LogMCPBlueprintManager, Log, All);

// Static member definitions
UMCPBlueprintManager* UMCPBlueprintManager::SingletonInstance = nullptr;
const FString UMCPBlueprintManager::DefaultAssetPath = TEXT("/Game/Blueprints/");

// Supported parent classes for blueprint creation
const TArray<FString> UMCPBlueprintManager::SupportedParentClasses = {
	TEXT("Actor"),
	TEXT("Pawn"),
	TEXT("Character"),
	TEXT("ActorComponent"),
	TEXT("SceneComponent"),
	TEXT("UserWidget"),
	TEXT("Object")
};

UMCPBlueprintManager::UMCPBlueprintManager()
	: MCPSettings(nullptr)
	, bIsInitialized(false)
	, AssetNameCounter(0)
{
}

UMCPBlueprintManager::~UMCPBlueprintManager()
{
	// Clear singleton reference
	if (SingletonInstance == this)
	{
		SingletonInstance = nullptr;
	}
}

void UMCPBlueprintManager::BeginDestroy()
{
	// Cleanup before destruction
	bIsInitialized = false;
	Super::BeginDestroy();
}

UMCPBlueprintManager* UMCPBlueprintManager::Get()
{
	if (!SingletonInstance)
	{
		SingletonInstance = NewObject<UMCPBlueprintManager>();
		SingletonInstance->AddToRoot(); // Prevent garbage collection
	}
	return SingletonInstance;
}

bool UMCPBlueprintManager::Initialize(UMCPSettings* InSettings)
{
	// Use provided settings or get default instance
	MCPSettings = InSettings ? InSettings : UMCPSettings::Get();

	if (!MCPSettings)
	{
		LogMessage(TEXT("Failed to initialize MCPBlueprintManager: No valid settings found"), ELogVerbosity::Error);
		return false;
	}

#if !WITH_EDITOR
	LogMessage(TEXT("MCPBlueprintManager requires editor environment"), ELogVerbosity::Error);
	return false;
#endif

	bIsInitialized = true;
	LogMessage(TEXT("MCPBlueprintManager initialized successfully"));
	return true;
}

FMCPBlueprintOperationResult UMCPBlueprintManager::CreateBlueprint(const FMCPBlueprintCreateParams& CreateParams)
{
#if WITH_EDITOR
	// Validate parameters
	FString ErrorMessage;
	if (!ValidateCreateParams(CreateParams, ErrorMessage))
	{
		LogMessage(FString::Printf(TEXT("Blueprint creation validation failed: %s"), *ErrorMessage), ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Find parent class
	UClass* ParentClass = FindClassByName(CreateParams.ParentClassName);
	if (!ParentClass)
	{
		ErrorMessage = FString::Printf(TEXT("Parent class '%s' not found"), *CreateParams.ParentClassName);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Check if class is blueprintable
	if (!IsClassBluepritable(ParentClass))
	{
		ErrorMessage = FString::Printf(TEXT("Class '%s' is not blueprintable"), *CreateParams.ParentClassName);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Create full asset path
	FString FullAssetPath = CreateParams.AssetPath;
	if (!FullAssetPath.EndsWith(TEXT("/")))
	{
		FullAssetPath += TEXT("/");
	}
	FullAssetPath += CreateParams.BlueprintName;

	// Create package
	UPackage* Package = CreateBlueprintPackage(FullAssetPath);
	if (!Package)
	{
		ErrorMessage = FString::Printf(TEXT("Failed to create package for path: %s"), *FullAssetPath);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Create blueprint
	UBlueprint* NewBlueprint = FKismetEditorUtilities::CreateBlueprint(
		ParentClass,
		Package,
		*CreateParams.BlueprintName,
		BPTYPE_Normal,
		UBlueprint::StaticClass(),
		UBlueprintGeneratedClass::StaticClass()
	);

	if (!NewBlueprint)
	{
		ErrorMessage = FString::Printf(TEXT("Failed to create blueprint: %s"), *CreateParams.BlueprintName);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Register asset and mark package dirty
	RegisterBlueprintAsset(NewBlueprint);
	Package->MarkPackageDirty();

	// Log success
	LogMessage(FString::Printf(TEXT("Successfully created blueprint: %s"), *FullAssetPath));

	return FMCPBlueprintOperationResult(true, TEXT(""), FullAssetPath);

#else
	LogMessage(TEXT("Blueprint creation requires editor environment"), ELogVerbosity::Error);
	return FMCPBlueprintOperationResult(false, TEXT("Editor environment required"));
#endif
}

FMCPBlueprintOperationResult UMCPBlueprintManager::SetBlueprintProperty(const FMCPBlueprintPropertyParams& PropertyParams)
{
#if WITH_EDITOR
	// Validate parameters
	FString ErrorMessage;
	if (!ValidatePropertyParams(PropertyParams, ErrorMessage))
	{
		LogMessage(FString::Printf(TEXT("Property modification validation failed: %s"), *ErrorMessage), ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Load blueprint asset
	UBlueprint* Blueprint = LoadBlueprintAsset(PropertyParams.BlueprintPath);
	if (!Blueprint)
	{
		ErrorMessage = FString::Printf(TEXT("Failed to load blueprint: %s"), *PropertyParams.BlueprintPath);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Get CDO
	UObject* CDO = GetBlueprintCDO(Blueprint);
	if (!CDO)
	{
		ErrorMessage = FString::Printf(TEXT("Failed to get CDO for blueprint: %s"), *PropertyParams.BlueprintPath);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Set property
	if (!SetPropertyValue(CDO, PropertyParams.PropertyName, PropertyParams.PropertyValue, PropertyParams.PropertyType))
	{
		ErrorMessage = FString::Printf(TEXT("Failed to set property '%s' on blueprint: %s"),
			*PropertyParams.PropertyName, *PropertyParams.BlueprintPath);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Mark blueprint as modified
	Blueprint->MarkPackageDirty();

	// Log success
	LogMessage(FString::Printf(TEXT("Successfully set property '%s' = '%s' on blueprint: %s"),
		*PropertyParams.PropertyName, *PropertyParams.PropertyValue, *PropertyParams.BlueprintPath));

	return FMCPBlueprintOperationResult(true, TEXT(""), PropertyParams.BlueprintPath);

#else
	LogMessage(TEXT("Property modification requires editor environment"), ELogVerbosity::Error);
	return FMCPBlueprintOperationResult(false, TEXT("Editor environment required"));
#endif
}

FString UMCPBlueprintManager::ProcessCreateBlueprintCommand(const FString& JsonCommand)
{
	FMCPBlueprintCreateParams CreateParams;

	// Parse JSON command
	if (!ParseCreateBlueprintJson(JsonCommand, CreateParams))
	{
		FMCPBlueprintOperationResult ErrorResult(false, TEXT("Failed to parse JSON command"));
		return CreateJsonResponse(ErrorResult);
	}

	// Execute blueprint creation
	FMCPBlueprintOperationResult Result = CreateBlueprint(CreateParams);

	// Return JSON response
	return CreateJsonResponse(Result);
}

FString UMCPBlueprintManager::ProcessSetPropertyCommand(const FString& JsonCommand)
{
	FMCPBlueprintPropertyParams PropertyParams;

	// Parse JSON command
	if (!ParseSetPropertyJson(JsonCommand, PropertyParams))
	{
		FMCPBlueprintOperationResult ErrorResult(false, TEXT("Failed to parse JSON command"));
		return CreateJsonResponse(ErrorResult);
	}

	// Execute property modification
	FMCPBlueprintOperationResult Result = SetBlueprintProperty(PropertyParams);

	// Return JSON response
	return CreateJsonResponse(Result);
}

TArray<FString> UMCPBlueprintManager::GetAvailableParentClasses() const
{
	return SupportedParentClasses;
}

bool UMCPBlueprintManager::ValidateCreateParams(const FMCPBlueprintCreateParams& CreateParams, FString& OutErrorMessage) const
{
	// Check blueprint name
	if (CreateParams.BlueprintName.IsEmpty())
	{
		OutErrorMessage = TEXT("Blueprint name cannot be empty");
		return false;
	}

	if (!IsValidBlueprintName(CreateParams.BlueprintName))
	{
		OutErrorMessage = TEXT("Blueprint name contains invalid characters");
		return false;
	}

	// Check parent class name
	if (CreateParams.ParentClassName.IsEmpty())
	{
		OutErrorMessage = TEXT("Parent class name cannot be empty");
		return false;
	}

	// Check asset path
	if (!IsValidAssetPath(CreateParams.AssetPath))
	{
		OutErrorMessage = TEXT("Invalid asset path");
		return false;
	}

	return true;
}

bool UMCPBlueprintManager::ValidatePropertyParams(const FMCPBlueprintPropertyParams& PropertyParams, FString& OutErrorMessage) const
{
	// Check blueprint path
	if (PropertyParams.BlueprintPath.IsEmpty())
	{
		OutErrorMessage = TEXT("Blueprint path cannot be empty");
		return false;
	}

	// Check property name
	if (PropertyParams.PropertyName.IsEmpty())
	{
		OutErrorMessage = TEXT("Property name cannot be empty");
		return false;
	}

	// Property value can be empty (for clearing values)
	// Property type is optional for basic validation

	return true;
}

// Private helper implementations

UClass* UMCPBlueprintManager::FindClassByName(const FString& ClassName) const
{
#if WITH_EDITOR
	// Common class mappings
	if (ClassName == TEXT("Actor"))
	{
		return AActor::StaticClass();
	}
	else if (ClassName == TEXT("Pawn"))
	{
		return APawn::StaticClass();
	}
	else if (ClassName == TEXT("Character"))
	{
		return ACharacter::StaticClass();
	}
	else if (ClassName == TEXT("ActorComponent"))
	{
		return UActorComponent::StaticClass();
	}
	else if (ClassName == TEXT("SceneComponent"))
	{
		return USceneComponent::StaticClass();
	}
	else if (ClassName == TEXT("UserWidget"))
	{
		return UUserWidget::StaticClass();
	}
	else if (ClassName == TEXT("Object"))
	{
		return UObject::StaticClass();
	}

	// Try to find class by name using reflection
	UClass* FoundClass = FindObject<UClass>(ANY_PACKAGE, *ClassName);
	return FoundClass;
#else
	return nullptr;
#endif
}

UPackage* UMCPBlueprintManager::CreateBlueprintPackage(const FString& AssetPath) const
{
#if WITH_EDITOR
	// Create package
	UPackage* Package = CreatePackage(*AssetPath);
	if (Package)
	{
		Package->FullyLoad();
	}
	return Package;
#else
	return nullptr;
#endif
}

void UMCPBlueprintManager::RegisterBlueprintAsset(UBlueprint* Blueprint) const
{
#if WITH_EDITOR
	if (Blueprint)
	{
		FAssetRegistryModule::AssetCreated(Blueprint);
	}
#endif
}

UBlueprint* UMCPBlueprintManager::LoadBlueprintAsset(const FString& BlueprintPath) const
{
#if WITH_EDITOR
	return LoadObject<UBlueprint>(nullptr, *BlueprintPath);
#else
	return nullptr;
#endif
}

UObject* UMCPBlueprintManager::GetBlueprintCDO(UBlueprint* Blueprint) const
{
#if WITH_EDITOR
	if (Blueprint && Blueprint->GeneratedClass)
	{
		return Blueprint->GeneratedClass->GetDefaultObject();
	}
#endif
	return nullptr;
}

bool UMCPBlueprintManager::SetPropertyValue(UObject* Object, const FString& PropertyName, const FString& PropertyValue, const FString& PropertyType) const
{
#if WITH_EDITOR
	if (!Object)
	{
		return false;
	}

	// Find property by name
	const FProperty* Property = Object->GetClass()->FindPropertyByName(*PropertyName);
	if (!Property)
	{
		LogMessage(FString::Printf(TEXT("Property '%s' not found in class '%s'"),
			*PropertyName, *Object->GetClass()->GetName()), ELogVerbosity::Warning);
		return false;
	}

	// Convert string value to property data
	uint8* PropertyData = Property->ContainerPtrToValuePtr<uint8>(Object);
	return ConvertStringToPropertyValue(Property, PropertyValue, PropertyData);
#else
	return false;
#endif
}

bool UMCPBlueprintManager::ConvertStringToPropertyValue(const FProperty* Property, const FString& StringValue, void* OutData) const
{
#if WITH_EDITOR
	if (!Property || !OutData)
	{
		return false;
	}

	// Handle different property types
	if (const FIntProperty* IntProp = CastField<FIntProperty>(Property))
	{
		int32 Value = FCString::Atoi(*StringValue);
		IntProp->SetPropertyValue(OutData, Value);
		return true;
	}
	else if (const FFloatProperty* FloatProp = CastField<FFloatProperty>(Property))
	{
		float Value = FCString::Atof(*StringValue);
		FloatProp->SetPropertyValue(OutData, Value);
		return true;
	}
	else if (const FBoolProperty* BoolProp = CastField<FBoolProperty>(Property))
	{
		bool Value = StringValue.ToBool();
		BoolProp->SetPropertyValue(OutData, Value);
		return true;
	}
	else if (const FStrProperty* StrProp = CastField<FStrProperty>(Property))
	{
		StrProp->SetPropertyValue(OutData, StringValue);
		return true;
	}
	else if (const FNameProperty* NameProp = CastField<FNameProperty>(Property))
	{
		FName Value(*StringValue);
		NameProp->SetPropertyValue(OutData, Value);
		return true;
	}
	else if (const FStructProperty* StructProp = CastField<FStructProperty>(Property))
	{
		// Handle common struct types
		if (StructProp->Struct == TBaseStructure<FVector>::Get())
		{
			FVector Vector;
			if (Vector.InitFromString(StringValue))
			{
				FVector* VectorPtr = StructProp->ContainerPtrToValuePtr<FVector>(OutData);
				if (VectorPtr)
				{
					*VectorPtr = Vector;
				}
				return true;
			}
		}
		else if (StructProp->Struct == TBaseStructure<FRotator>::Get())
		{
			FRotator Rotator;
			if (Rotator.InitFromString(StringValue))
			{
				FRotator* RotatorPtr = StructProp->ContainerPtrToValuePtr<FRotator>(OutData);
				if (RotatorPtr)
				{
					*RotatorPtr = Rotator;
				}
				return true;
			}
		}
	}

	LogMessage(FString::Printf(TEXT("Unsupported property type: %s"), *Property->GetClass()->GetName()), ELogVerbosity::Warning);
	return false;
#else
	return false;
#endif
}

// JSON helper implementations

bool UMCPBlueprintManager::ParseCreateBlueprintJson(const FString& JsonCommand, FMCPBlueprintCreateParams& OutParams) const
{
	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonCommand);

	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		return false;
	}

	// Parse parameters
	OutParams.BlueprintName = JsonObject->GetStringField(TEXT("blueprint_name"));
	OutParams.ParentClassName = JsonObject->GetStringField(TEXT("parent_class"));

	FString AssetPath = JsonObject->GetStringField(TEXT("asset_path"));
	if (!AssetPath.IsEmpty())
	{
		OutParams.AssetPath = AssetPath;
	}

	return true;
}

bool UMCPBlueprintManager::ParseSetPropertyJson(const FString& JsonCommand, FMCPBlueprintPropertyParams& OutParams) const
{
	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonCommand);

	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		return false;
	}

	// Parse parameters
	OutParams.BlueprintPath = JsonObject->GetStringField(TEXT("blueprint_path"));
	OutParams.PropertyName = JsonObject->GetStringField(TEXT("property_name"));
	OutParams.PropertyValue = JsonObject->GetStringField(TEXT("property_value"));
	OutParams.PropertyType = JsonObject->GetStringField(TEXT("property_type"));

	return true;
}

FString UMCPBlueprintManager::CreateJsonResponse(const FMCPBlueprintOperationResult& Result) const
{
	TSharedPtr<FJsonObject> ResponseObject = MakeShareable(new FJsonObject);

	ResponseObject->SetBoolField(TEXT("success"), Result.bSuccess);
	ResponseObject->SetStringField(TEXT("error_message"), Result.ErrorMessage);
	ResponseObject->SetStringField(TEXT("blueprint_path"), Result.BlueprintPath);
	ResponseObject->SetStringField(TEXT("result_data"), Result.ResultData);
	ResponseObject->SetStringField(TEXT("timestamp"), FDateTime::Now().ToString());

	FString OutputString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
	if (!FJsonSerializer::Serialize(ResponseObject.ToSharedRef(), Writer))
	{
		UE_LOG(LogMCPBlueprintManager, Warning, TEXT("Failed to serialize JSON response"));
	}

	return OutputString;
}

// Validation helper implementations

bool UMCPBlueprintManager::IsValidAssetPath(const FString& AssetPath) const
{
	// Basic validation - should start with /Game/
	if (!AssetPath.StartsWith(TEXT("/Game/")))
	{
		return false;
	}

	// Check for invalid characters
	const FString InvalidChars = TEXT("<>:\"|?*");
	for (const TCHAR& Char : InvalidChars)
	{
		if (AssetPath.Contains(FString::Chr(Char)))
		{
			return false;
		}
	}

	return true;
}

bool UMCPBlueprintManager::IsValidBlueprintName(const FString& BlueprintName) const
{
	// Basic name validation
	if (BlueprintName.IsEmpty() || BlueprintName.Len() > 64)
	{
		return false;
	}

	// Should start with letter or underscore
	TCHAR FirstChar = BlueprintName[0];
	if (!FChar::IsAlpha(FirstChar) && FirstChar != TEXT('_'))
	{
		return false;
	}

	// Should contain only alphanumeric characters and underscores
	for (const TCHAR& Char : BlueprintName)
	{
		if (!FChar::IsAlnum(Char) && Char != TEXT('_'))
		{
			return false;
		}
	}

	return true;
}

bool UMCPBlueprintManager::IsClassBluepritable(UClass* Class) const
{
#if WITH_EDITOR
	if (!Class)
	{
		return false;
	}

	// Check if class is blueprintable (not abstract, deprecated, or interface)
	return !Class->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated | CLASS_Interface);
#else
	return false;
#endif
}

void UMCPBlueprintManager::LogMessage(const FString& Message, ELogVerbosity::Type Verbosity) const
{
	// Use appropriate log level based on verbosity
	switch (Verbosity)
	{
		case ELogVerbosity::Error:
			UE_LOG(LogMCPBlueprintManager, Error, TEXT("[MCPBlueprintManager] %s"), *Message);
			break;
		case ELogVerbosity::Warning:
			UE_LOG(LogMCPBlueprintManager, Warning, TEXT("[MCPBlueprintManager] %s"), *Message);
			break;
		default:
			UE_LOG(LogMCPBlueprintManager, Log, TEXT("[MCPBlueprintManager] %s"), *Message);
			break;
	}
}

FString UMCPBlueprintManager::ProcessAddComponentCommand(const FString& JsonCommand)
{
	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonCommand);

	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		FMCPBlueprintOperationResult ErrorResult(false, TEXT("Failed to parse JSON command"));
		return CreateJsonResponse(ErrorResult);
	}

	// Parse parameters
	FString BlueprintPath = JsonObject->GetStringField(TEXT("blueprint_path"));
	FString ComponentType = JsonObject->GetStringField(TEXT("component_type"));
	FString ComponentName = JsonObject->GetStringField(TEXT("component_name"));

	// Execute component addition
	FMCPBlueprintOperationResult Result = AddComponentToBlueprint(BlueprintPath, ComponentType, ComponentName);

	// Return JSON response
	return CreateJsonResponse(Result);
}

FString UMCPBlueprintManager::ProcessCompileBlueprintCommand(const FString& JsonCommand)
{
	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonCommand);

	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		FMCPBlueprintOperationResult ErrorResult(false, TEXT("Failed to parse JSON command"));
		return CreateJsonResponse(ErrorResult);
	}

	// Parse parameters
	FString BlueprintPath = JsonObject->GetStringField(TEXT("blueprint_path"));

	// Execute blueprint compilation
	FMCPBlueprintOperationResult Result = CompileBlueprint(BlueprintPath);

	// Return JSON response
	return CreateJsonResponse(Result);
}

FString UMCPBlueprintManager::ProcessGetServerStatusCommand(const FString& JsonCommand)
{
	// Return server status information
	return GetServerStatus();
}

FMCPBlueprintOperationResult UMCPBlueprintManager::AddComponentToBlueprint(const FString& BlueprintPath, const FString& ComponentType, const FString& ComponentName)
{
#if WITH_EDITOR
	// Validate inputs
	if (BlueprintPath.IsEmpty() || ComponentType.IsEmpty() || ComponentName.IsEmpty())
	{
		FString ErrorMessage = TEXT("Blueprint path, component type, and component name cannot be empty");
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Load blueprint asset
	UBlueprint* Blueprint = LoadBlueprintAsset(BlueprintPath);
	if (!Blueprint)
	{
		FString ErrorMessage = FString::Printf(TEXT("Failed to load blueprint: %s"), *BlueprintPath);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Find component class
	UClass* ComponentClass = FindObject<UClass>(ANY_PACKAGE, *ComponentType);
	if (!ComponentClass)
	{
		// Try with "Component" suffix if not found
		FString ComponentTypeWithSuffix = ComponentType + TEXT("Component");
		ComponentClass = FindObject<UClass>(ANY_PACKAGE, *ComponentTypeWithSuffix);
	}

	if (!ComponentClass)
	{
		FString ErrorMessage = FString::Printf(TEXT("Component class not found: %s"), *ComponentType);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Check if it's a valid component class
	if (!ComponentClass->IsChildOf(UActorComponent::StaticClass()))
	{
		FString ErrorMessage = FString::Printf(TEXT("Class %s is not a component class"), *ComponentType);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Get or create the Simple Construction Script
	USimpleConstructionScript* SCS = Blueprint->SimpleConstructionScript;
	if (!SCS)
	{
		SCS = NewObject<USimpleConstructionScript>(Blueprint);
		Blueprint->SimpleConstructionScript = SCS;
	}

	// Create new SCS node for the component
	USCS_Node* NewNode = SCS->CreateNode(ComponentClass, FName(*ComponentName));
	if (!NewNode)
	{
		FString ErrorMessage = FString::Printf(TEXT("Failed to create SCS node for component %s in blueprint %s"), *ComponentName, *BlueprintPath);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Add the node to the construction script
	SCS->AddNode(NewNode);

	// Get the component template from the node
	UActorComponent* NewComponent = NewNode->ComponentTemplate;

	// Mark blueprint as modified
	Blueprint->MarkPackageDirty();

	// Log success
	LogMessage(FString::Printf(TEXT("Successfully added component '%s' of type '%s' to blueprint: %s"),
		*ComponentName, *ComponentType, *BlueprintPath));

	return FMCPBlueprintOperationResult(true, TEXT(""), BlueprintPath);

#else
	LogMessage(TEXT("Component addition requires editor environment"), ELogVerbosity::Error);
	return FMCPBlueprintOperationResult(false, TEXT("Editor environment required"));
#endif
}

FMCPBlueprintOperationResult UMCPBlueprintManager::CompileBlueprint(const FString& BlueprintPath)
{
#if WITH_EDITOR
	// Validate input
	if (BlueprintPath.IsEmpty())
	{
		FString ErrorMessage = TEXT("Blueprint path cannot be empty");
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Load blueprint asset
	UBlueprint* Blueprint = LoadBlueprintAsset(BlueprintPath);
	if (!Blueprint)
	{
		FString ErrorMessage = FString::Printf(TEXT("Failed to load blueprint: %s"), *BlueprintPath);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Compile the blueprint
	FKismetEditorUtilities::CompileBlueprint(Blueprint);

	// Check for compilation errors
	if (Blueprint->Status == BS_Error)
	{
		FString ErrorMessage = FString::Printf(TEXT("Blueprint compilation failed: %s"), *BlueprintPath);
		LogMessage(ErrorMessage, ELogVerbosity::Error);
		return FMCPBlueprintOperationResult(false, ErrorMessage);
	}

	// Log success
	LogMessage(FString::Printf(TEXT("Successfully compiled blueprint: %s"), *BlueprintPath));

	return FMCPBlueprintOperationResult(true, TEXT(""), BlueprintPath);

#else
	LogMessage(TEXT("Blueprint compilation requires editor environment"), ELogVerbosity::Error);
	return FMCPBlueprintOperationResult(false, TEXT("Editor environment required"));
#endif
}

FString UMCPBlueprintManager::GetServerStatus() const
{
	TSharedPtr<FJsonObject> StatusObject = MakeShareable(new FJsonObject);

	// Basic server information
	StatusObject->SetBoolField(TEXT("online"), true);
	StatusObject->SetStringField(TEXT("version"), TEXT("1.0.0"));
	StatusObject->SetStringField(TEXT("plugin_name"), TEXT("UnrealBlueprintMCP"));
	StatusObject->SetStringField(TEXT("timestamp"), FDateTime::Now().ToString());
	StatusObject->SetBoolField(TEXT("editor_available"), WITH_EDITOR ? true : false);
	StatusObject->SetBoolField(TEXT("initialized"), bIsInitialized);

	// Supported operations
	TArray<TSharedPtr<FJsonValue>> SupportedOperations;
	SupportedOperations.Add(MakeShareable(new FJsonValueString(TEXT("create_blueprint"))));
	SupportedOperations.Add(MakeShareable(new FJsonValueString(TEXT("set_property"))));
	SupportedOperations.Add(MakeShareable(new FJsonValueString(TEXT("add_component"))));
	SupportedOperations.Add(MakeShareable(new FJsonValueString(TEXT("compile_blueprint"))));
	SupportedOperations.Add(MakeShareable(new FJsonValueString(TEXT("get_server_status"))));
	StatusObject->SetArrayField(TEXT("supported_operations"), SupportedOperations);

	// Supported parent classes
	TArray<TSharedPtr<FJsonValue>> ParentClasses;
	for (const FString& ClassName : SupportedParentClasses)
	{
		ParentClasses.Add(MakeShareable(new FJsonValueString(ClassName)));
	}
	StatusObject->SetArrayField(TEXT("supported_parent_classes"), ParentClasses);

	// Serialize to string
	FString OutputString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
	if (!FJsonSerializer::Serialize(StatusObject.ToSharedRef(), Writer))
	{
		UE_LOG(LogMCPBlueprintManager, Warning, TEXT("Failed to serialize server status JSON"));
	}

	return OutputString;
}