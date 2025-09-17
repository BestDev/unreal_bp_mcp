// Copyright Epic Games, Inc. All Rights Reserved.
// MCPBlueprintManager - Handles blueprint creation and property modification for MCP protocol

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "Engine/Blueprint.h"
#include "UnrealBlueprintMCPAPI.h"
#include "Dom/JsonObject.h"
#include "MCPBlueprintManager.generated.h"

class UMCPSettings;

/**
 * Result structure for blueprint operations
 */
USTRUCT(BlueprintType)
struct UNREALBLUEPRINTMCP_API FMCPBlueprintOperationResult
{
	GENERATED_BODY()

	/** Whether the operation was successful */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Operation")
	bool bSuccess;

	/** Error message if operation failed */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Operation")
	FString ErrorMessage;

	/** Path to the created/modified blueprint asset */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Operation")
	FString BlueprintPath;

	/** Additional result data as JSON string */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Operation")
	FString ResultData;

	/** Default constructor */
	FMCPBlueprintOperationResult()
		: bSuccess(false)
	{
	}

	/** Constructor with result */
	FMCPBlueprintOperationResult(bool InSuccess, const FString& InErrorMessage = TEXT(""), const FString& InBlueprintPath = TEXT(""))
		: bSuccess(InSuccess)
		, ErrorMessage(InErrorMessage)
		, BlueprintPath(InBlueprintPath)
	{
	}
};

/**
 * Structure representing blueprint creation parameters
 */
USTRUCT(BlueprintType)
struct UNREALBLUEPRINTMCP_API FMCPBlueprintCreateParams
{
	GENERATED_BODY()

	/** Name of the blueprint to create */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Create")
	FString BlueprintName;

	/** Parent class name (e.g., "Actor", "Pawn", "UserWidget") */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Create")
	FString ParentClassName;

	/** Asset path where to create the blueprint (e.g., "/Game/Blueprints/") */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Create")
	FString AssetPath;

	/** Default constructor */
	FMCPBlueprintCreateParams()
		: AssetPath(TEXT("/Game/Blueprints/"))
	{
	}
};

/**
 * Structure representing blueprint property modification parameters
 */
USTRUCT(BlueprintType)
struct UNREALBLUEPRINTMCP_API FMCPBlueprintPropertyParams
{
	GENERATED_BODY()

	/** Path to the blueprint asset */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Property")
	FString BlueprintPath;

	/** Name of the property to modify */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Property")
	FString PropertyName;

	/** New value for the property as string */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Property")
	FString PropertyValue;

	/** Type of the property (for validation) */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Blueprint Property")
	FString PropertyType;

	/** Default constructor */
	FMCPBlueprintPropertyParams()
	{
	}
};

/**
 * Manager class for handling MCP blueprint operations.
 *
 * This class provides functionality to create blueprints and modify their properties
 * programmatically through the MCP protocol. It handles JSON message parsing,
 * blueprint creation using UE5.6 APIs, and property modification through CDO access.
 *
 * Key features:
 * - Blueprint creation with various parent classes
 * - Property modification through reflection
 * - Error handling and validation
 * - JSON-based parameter parsing
 * - Editor-only functionality with WITH_EDITOR guards
 */
UCLASS(BlueprintType, Blueprintable)
class UNREALBLUEPRINTMCP_API UMCPBlueprintManager : public UObject
{
	GENERATED_BODY()

public:
	/** Constructor */
	UMCPBlueprintManager();

	/** Destructor */
	virtual ~UMCPBlueprintManager();

	//~ Begin UObject Interface
	virtual void BeginDestroy() override;
	//~ End UObject Interface

	/**
	 * Get the singleton instance of MCPBlueprintManager
	 * @return The singleton MCPBlueprintManager instance
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Blueprint Manager")
	static UMCPBlueprintManager* Get();

	/**
	 * Initialize the blueprint manager with settings
	 * @param InSettings The MCP settings to use for configuration
	 * @return True if initialization was successful
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	bool Initialize(UMCPSettings* InSettings = nullptr);

	/**
	 * Create a new blueprint asset
	 * @param CreateParams Parameters for blueprint creation
	 * @return Result of the operation
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FMCPBlueprintOperationResult CreateBlueprint(const FMCPBlueprintCreateParams& CreateParams);

	/**
	 * Set a property on an existing blueprint's CDO
	 * @param PropertyParams Parameters for property modification
	 * @return Result of the operation
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FMCPBlueprintOperationResult SetBlueprintProperty(const FMCPBlueprintPropertyParams& PropertyParams);

	/**
	 * Process a create_blueprint JSON command from MCP
	 * @param JsonCommand The JSON command object
	 * @return JSON response as string
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FString ProcessCreateBlueprintCommand(const FString& JsonCommand);

	/**
	 * Process a set_property JSON command from MCP
	 * @param JsonCommand The JSON command object
	 * @return JSON response as string
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FString ProcessSetPropertyCommand(const FString& JsonCommand);

	/**
	 * Process an add_component JSON command from MCP
	 * @param JsonCommand The JSON command object
	 * @return JSON response as string
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FString ProcessAddComponentCommand(const FString& JsonCommand);

	/**
	 * Process a compile_blueprint JSON command from MCP
	 * @param JsonCommand The JSON command object
	 * @return JSON response as string
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FString ProcessCompileBlueprintCommand(const FString& JsonCommand);

	/**
	 * Process a get_server_status JSON command from MCP
	 * @param JsonCommand The JSON command object
	 * @return JSON response as string
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FString ProcessGetServerStatusCommand(const FString& JsonCommand);

	/**
	 * Get list of available parent classes for blueprint creation
	 * @return Array of class names that can be used as blueprint parents
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Blueprint Manager")
	TArray<FString> GetAvailableParentClasses() const;

	/**
	 * Validate blueprint creation parameters
	 * @param CreateParams Parameters to validate
	 * @param OutErrorMessage Error message if validation fails
	 * @return True if parameters are valid
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Blueprint Manager")
	bool ValidateCreateParams(const FMCPBlueprintCreateParams& CreateParams, FString& OutErrorMessage) const;

	/**
	 * Validate property modification parameters
	 * @param PropertyParams Parameters to validate
	 * @param OutErrorMessage Error message if validation fails
	 * @return True if parameters are valid
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Blueprint Manager")
	bool ValidatePropertyParams(const FMCPBlueprintPropertyParams& PropertyParams, FString& OutErrorMessage) const;

	/**
	 * Add a component to an existing blueprint
	 * @param BlueprintPath Path to the blueprint asset
	 * @param ComponentType Type of component to add (e.g., "StaticMeshComponent")
	 * @param ComponentName Name for the new component
	 * @return Result of the operation
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FMCPBlueprintOperationResult AddComponentToBlueprint(const FString& BlueprintPath, const FString& ComponentType, const FString& ComponentName);

	/**
	 * Compile an existing blueprint
	 * @param BlueprintPath Path to the blueprint asset
	 * @return Result of the operation
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FMCPBlueprintOperationResult CompileBlueprint(const FString& BlueprintPath);

	/**
	 * Get server status information
	 * @return JSON string with server status
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Blueprint Manager")
	FString GetServerStatus() const;

private:
	// Blueprint creation helpers

	/**
	 * Find UClass by name for blueprint parent class
	 * @param ClassName Name of the class to find
	 * @return Pointer to the class or nullptr if not found
	 */
	UClass* FindClassByName(const FString& ClassName) const;

	/**
	 * Create package for blueprint asset
	 * @param AssetPath Full path for the asset
	 * @return Created package or nullptr if failed
	 */
	UPackage* CreateBlueprintPackage(const FString& AssetPath) const;

	/**
	 * Register newly created asset with asset registry
	 * @param Blueprint The blueprint asset to register
	 */
	void RegisterBlueprintAsset(UBlueprint* Blueprint) const;

	// Property modification helpers

	/**
	 * Load blueprint asset from path
	 * @param BlueprintPath Path to the blueprint asset
	 * @return Loaded blueprint or nullptr if failed
	 */
	UBlueprint* LoadBlueprintAsset(const FString& BlueprintPath) const;

	/**
	 * Get CDO from blueprint for property modification
	 * @param Blueprint The blueprint to get CDO from
	 * @return CDO object or nullptr if failed
	 */
	UObject* GetBlueprintCDO(UBlueprint* Blueprint) const;

	/**
	 * Set property value using reflection
	 * @param Object Target object
	 * @param PropertyName Name of the property
	 * @param PropertyValue Value as string
	 * @param PropertyType Expected property type
	 * @return True if property was set successfully
	 */
	bool SetPropertyValue(UObject* Object, const FString& PropertyName, const FString& PropertyValue, const FString& PropertyType) const;

	/**
	 * Convert string value to appropriate property type
	 * @param Property The property descriptor
	 * @param StringValue Value as string
	 * @param OutData Output data buffer
	 * @return True if conversion was successful
	 */
	bool ConvertStringToPropertyValue(const FProperty* Property, const FString& StringValue, void* OutData) const;

	// JSON helpers

	/**
	 * Parse JSON command into create params
	 * @param JsonCommand JSON command string
	 * @param OutParams Output parameters
	 * @return True if parsing was successful
	 */
	bool ParseCreateBlueprintJson(const FString& JsonCommand, FMCPBlueprintCreateParams& OutParams) const;

	/**
	 * Parse JSON command into property params
	 * @param JsonCommand JSON command string
	 * @param OutParams Output parameters
	 * @return True if parsing was successful
	 */
	bool ParseSetPropertyJson(const FString& JsonCommand, FMCPBlueprintPropertyParams& OutParams) const;

	/**
	 * Create JSON response for operation result
	 * @param Result The operation result
	 * @return JSON response string
	 */
	FString CreateJsonResponse(const FMCPBlueprintOperationResult& Result) const;

	// Validation helpers

	/**
	 * Check if asset path is valid and writable
	 * @param AssetPath Path to validate
	 * @return True if path is valid
	 */
	bool IsValidAssetPath(const FString& AssetPath) const;

	/**
	 * Check if blueprint name is valid
	 * @param BlueprintName Name to validate
	 * @return True if name is valid
	 */
	bool IsValidBlueprintName(const FString& BlueprintName) const;

	/**
	 * Check if class is blueprintable
	 * @param Class Class to check
	 * @return True if class can be used as blueprint parent
	 */
	bool IsClassBluepritable(UClass* Class) const;

	// Utility functions

	/**
	 * Log a message with MCP Blueprint Manager prefix
	 * @param Message Message to log
	 * @param Verbosity Log verbosity level
	 */
	void LogMessage(const FString& Message, ELogVerbosity::Type Verbosity = ELogVerbosity::Log) const;

private:
	// Core components

	/** Reference to MCP settings */
	UPROPERTY(Transient)
	UMCPSettings* MCPSettings;

	// State management

	/** Whether the manager is initialized */
	bool bIsInitialized;

	/** Counter for generating unique asset names */
	int32 AssetNameCounter;

	// Constants

	/** Default blueprint asset path */
	static const FString DefaultAssetPath;

	/** Supported parent class names */
	static const TArray<FString> SupportedParentClasses;

	/** Singleton instance */
	static UMCPBlueprintManager* SingletonInstance;
};