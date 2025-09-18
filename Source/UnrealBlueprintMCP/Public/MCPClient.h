// Copyright Epic Games, Inc. All Rights Reserved.
// MCPClient - WebSocket client for MCP server communication

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "IWebSocket.h"
#include "Dom/JsonObject.h"
#include "MCPSettings.h"
#include "UnrealBlueprintMCPAPI.h"
#include "MCPClient.generated.h"

class SMCPStatusWidget;
class FWebSocketsModule;
class UMCPBlueprintManager;

/**
 * Delegate for connection state changes
 * @param NewState The new connection state
 * @param ErrorMessage Optional error message if connection failed
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnMCPConnectionStateChanged, EMCPConnectionState, NewState, const FString&, ErrorMessage);

/**
 * Delegate for incoming MCP messages
 * @param MessageType The type of MCP message received
 * @param MessageData The JSON data of the message
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnMCPMessageReceived, const FString&, MessageType, const FString&, MessageData);

/**
 * Delegate for MCP operation responses
 * @param RequestId The ID of the original request
 * @param bSuccess Whether the operation was successful
 * @param ResponseData The response data as JSON string
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnMCPOperationComplete, const FString&, RequestId, bool, bSuccess, const FString&, ResponseData);

/**
 * Structure representing an MCP message for sending/receiving
 */
USTRUCT(BlueprintType)
struct UNREALBLUEPRINTMCP_API FMCPMessage
{
	GENERATED_BODY()

	/** Unique identifier for the message */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Message")
	FString Id;

	/** Type of the MCP message (request, response, notification) */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Message")
	FString Type;

	/** Method name for requests */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Message")
	FString Method;

	/** Parameters as JSON string */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Message")
	FString Params;

	/** Result data for responses */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Message")
	FString Result;

	/** Error information if any */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Message")
	FString Error;

	/** Timestamp when message was created */
	UPROPERTY(BlueprintReadWrite, Category = "MCP Message")
	FDateTime Timestamp;

	/** Default constructor */
	FMCPMessage()
		: Timestamp(FDateTime::Now())
	{
	}

	/** Constructor with basic fields */
	FMCPMessage(const FString& InId, const FString& InType, const FString& InMethod = TEXT(""))
		: Id(InId)
		, Type(InType)
		, Method(InMethod)
		, Timestamp(FDateTime::Now())
	{
	}
};

/**
 * WebSocket client for connecting to MCP (Model Context Protocol) servers.
 *
 * This class handles the WebSocket connection to external AI servers using the MCP protocol,
 * providing methods for sending requests, receiving responses, and managing connection state.
 * It integrates with the MCPSettings configuration and provides delegate events for UI updates.
 *
 * Key features:
 * - Automatic connection management with reconnection logic
 * - JSON message serialization/deserialization for MCP protocol
 * - Thread-safe operation with proper delegate dispatching
 * - Integration with MCPStatusWidget for real-time status updates
 * - Comprehensive error handling and logging
 */
UCLASS(BlueprintType, Blueprintable)
class UNREALBLUEPRINTMCP_API UMCPClient : public UObject
{
	GENERATED_BODY()

public:
	/** Constructor */
	UMCPClient();

	/** Destructor */
	virtual ~UMCPClient();

	//~ Begin UObject Interface
	virtual void BeginDestroy() override;
	//~ End UObject Interface

	/**
	 * Get the singleton instance of MCPClient
	 * @param bCreateIfNeeded Whether to create the instance if it doesn't exist
	 * @return The singleton MCPClient instance
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Client")
	static UMCPClient* Get(bool bCreateIfNeeded = true);

	/**
	 * Shutdown the singleton instance safely
	 */
	static void Shutdown();

	/**
	 * Check if the client is shutting down
	 * @return True if shutting down
	 */
	static bool IsShuttingDown() { return bIsShuttingDown; }

	/**
	 * Initialize the MCP client with settings
	 * @param InSettings The MCP settings to use for configuration
	 * @return True if initialization was successful
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Client")
	bool Initialize(UMCPSettings* InSettings = nullptr);

	/**
	 * Connect to the MCP server using current settings
	 * @return True if connection attempt was started successfully
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Client")
	bool Connect();

	/**
	 * Disconnect from the MCP server
	 * @param bGraceful Whether to perform a graceful disconnect
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Client")
	void Disconnect(bool bGraceful = true);

	/**
	 * Check if currently connected to MCP server
	 * @return True if connected
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Client")
	bool IsConnected() const;

	/**
	 * Get the current connection state
	 * @return Current connection state
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Client")
	EMCPConnectionState GetConnectionState() const;

	/**
	 * Send an MCP request message to the server
	 * @param Method The MCP method to call
	 * @param Params Parameters as JSON object
	 * @param RequestId Optional custom request ID (auto-generated if empty)
	 * @return The request ID for tracking the response
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Client")
	FString SendRequest(const FString& Method, const FString& Params, const FString& RequestId = TEXT(""));

	/**
	 * Send an MCP notification message to the server
	 * @param Method The MCP method name
	 * @param Params Parameters as JSON string
	 * @return True if message was sent successfully
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Client")
	bool SendNotification(const FString& Method, const FString& Params);

	/**
	 * Send a raw JSON message to the server
	 * @param JsonMessage The JSON message string to send
	 * @return True if message was sent successfully
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Client")
	bool SendRawMessage(const FString& JsonMessage);

	/**
	 * Register a status widget for receiving updates
	 * @param StatusWidget The widget to register for updates
	 */
	void RegisterStatusWidget(TSharedPtr<SMCPStatusWidget> StatusWidget);

	/**
	 * Unregister a status widget from receiving updates
	 * @param StatusWidget The widget to unregister
	 */
	void UnregisterStatusWidget(TSharedPtr<SMCPStatusWidget> StatusWidget);

	/**
	 * Set whether to enable automatic reconnection
	 * @param bEnable Whether to enable auto-reconnect
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Client")
	void SetAutoReconnectEnabled(bool bEnable);

	/**
	 * Get whether automatic reconnection is enabled
	 * @return True if auto-reconnect is enabled
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Client")
	bool IsAutoReconnectEnabled() const;

	/**
	 * Get the last error message if any
	 * @return The last error message
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Client")
	FString GetLastErrorMessage() const;

	/**
	 * Clear the last error message
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Client")
	void ClearLastError();

	/**
	 * Process blueprint-related MCP commands
	 * @param Method The MCP method (create_blueprint, set_property)
	 * @param Params Parameters as JSON string
	 * @return Response as JSON string
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Client")
	FString ProcessBlueprintCommand(const FString& Method, const FString& Params);

public:
	// Delegate events

	/** Event fired when connection state changes */
	UPROPERTY(BlueprintAssignable, Category = "MCP Client Events")
	FOnMCPConnectionStateChanged OnConnectionStateChanged;

	/** Event fired when an MCP message is received */
	UPROPERTY(BlueprintAssignable, Category = "MCP Client Events")
	FOnMCPMessageReceived OnMessageReceived;

	/** Event fired when an MCP operation completes */
	UPROPERTY(BlueprintAssignable, Category = "MCP Client Events")
	FOnMCPOperationComplete OnOperationComplete;

private:
	// WebSocket event handlers

	/** Called when WebSocket connection is established */
	void OnWebSocketConnected();

	/** Called when WebSocket connection fails */
	void OnWebSocketConnectionError(const FString& Error);

	/** Called when WebSocket connection is closed */
	void OnWebSocketClosed(int32 StatusCode, const FString& Reason, bool bWasClean);

	/** Called when a message is received from WebSocket */
	void OnWebSocketMessage(const FString& Message);

	/** Called when binary data is received (not used for MCP) */
	void OnWebSocketBinaryMessage(const void* Data, uint64 Size, bool bIsLastFragment);

	/** Called when a message is sent successfully */
	void OnWebSocketMessageSent(const FString& Message);

	// Connection management

	/** Update the connection state and notify listeners */
	void SetConnectionState(EMCPConnectionState NewState, const FString& ErrorMessage = TEXT(""));

	/** Start the auto-reconnect timer */
	void StartAutoReconnectTimer();

	/** Stop the auto-reconnect timer */
	void StopAutoReconnectTimer();

	/** Called by auto-reconnect timer */
	void AttemptReconnect();

	/** Reset reconnection attempt counter */
	void ResetReconnectAttempts();

	// Message handling

	/** Process an incoming MCP message */
	void ProcessIncomingMessage(const FString& JsonMessage);

	/** Parse a JSON message into an MCP message structure */
	bool ParseMCPMessage(const FString& JsonMessage, FMCPMessage& OutMessage);

	/** Create a JSON string from an MCP message */
	FString CreateJsonFromMCPMessage(const FMCPMessage& Message);

	/** Generate a unique request ID */
	FString GenerateRequestId();

	/** Validate MCP message format */
	bool ValidateMCPMessage(const FMCPMessage& Message);

	// Utility functions

	/** Log a message with MCP client prefix */
	void LogMessage(const FString& Message, ELogVerbosity::Type Verbosity = ELogVerbosity::Log);

	/** Notify registered status widgets of updates */
	void NotifyStatusWidgets(const FString& MessageLogLevel, const FString& LogMessage);

	/** Get the WebSocket URL from current settings */
	FString GetWebSocketURL() const;

	/** Check if settings are valid for connection */
	bool ValidateConnectionSettings() const;

private:
	// Core components

	/** Reference to MCP settings */
	UPROPERTY(Transient)
	UMCPSettings* MCPSettings;

	/** Reference to blueprint manager */
	UPROPERTY(Transient)
	UMCPBlueprintManager* BlueprintManager;

	/** WebSocket connection instance */
	TSharedPtr<IWebSocket> WebSocket;

	/** WebSockets module reference */
	FWebSocketsModule* WebSocketsModule;

	// State management

	/** Current connection state */
	EMCPConnectionState CurrentConnectionState;

	/** Last error message */
	FString LastErrorMessage;

	/** Whether auto-reconnect is enabled */
	bool bAutoReconnectEnabled;

	/** Number of reconnection attempts made */
	int32 ReconnectAttempts;

	/** Timer handle for auto-reconnect */
	FTimerHandle AutoReconnectTimerHandle;

	/** Timestamp of last connection attempt */
	FDateTime LastConnectionAttempt;

	// Message tracking

	/** Map of pending requests by ID */
	TMap<FString, FMCPMessage> PendingRequests;

	/** Counter for generating unique request IDs */
	int32 RequestIdCounter;

	/** Mutex for thread-safe access to pending requests */
	mutable FCriticalSection RequestsMutex;

	// UI integration

	/** Registered status widgets for updates */
	TArray<TWeakPtr<SMCPStatusWidget>> RegisteredStatusWidgets;

	/** Mutex for thread-safe access to status widgets */
	mutable FCriticalSection StatusWidgetsMutex;

	// Constants

	/** Maximum number of reconnection attempts */
	static const int32 MaxReconnectAttempts = 10;

	/** Base delay between reconnection attempts (seconds) */
	static const float BaseReconnectDelay;

	/** Maximum delay between reconnection attempts (seconds) */
	static const float MaxReconnectDelay;

	/** WebSocket connection timeout (seconds) */
	static const float ConnectionTimeout;

	/** MCP protocol version */
	static const FString MCPProtocolVersion;

	// Singleton instance
	static UMCPClient* SingletonInstance;

	// Shutdown state
	static bool bIsShuttingDown;
};