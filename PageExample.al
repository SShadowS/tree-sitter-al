page 9999999 "Sample E-Mail Templates"
{
    Caption = 'Sample Email Templates';
    ApplicationArea = All;
    SourceTable = "Sample E-Mail Template Header";
    PageType = List;
    UsageCategory = Lists;
    CardPageId = "Sample E-Mail Template Card";
    PromotedActionCategories = 'Manage,Process,Report,Template,Online,Import/Export';

    layout
    {
        area(Content)
        {
            repeater(TemplateLines)
            {
                field("1000000001"; TemplateCode)
                {
                    ApplicationArea = All;
                    ToolTip = 'Identifies the template.';
                }
                field("1000000007"; "Group")
                {
                    ApplicationArea = All;
                    ToolTip = 'Specifies the group for the template.';
                }
                field("1000000003"; "Report ID")
                {
                    ApplicationArea = All;
                    LookupPageId = "Sample NAV Objects";
                    ToolTip = 'Identifies the report number for this template.';
                }
                field("1000000005"; "Report Name")
                {
                    ApplicationArea = All;
                    ToolTip = 'Name of the report specified in Report ID.';
                }
                field("1"; "First Data Item")
                {
                    ApplicationArea = All;
                    ToolTip = 'Specifies the first data item in the report.';
                    Visible = false;
                }
                field("4"; "Data Item N.")
                {
                    ApplicationArea = All;
                    ToolTip = 'Specifies the table name for the first data item.';
                    Visible = false;
                }
                field("1000000009"; ProcessingEngine)
                {
                    ApplicationArea = All;
                    ToolTip = 'Specifies how the document is generated. Recommended method is Built-in PDF.';
                    Visible = false;
                }
                field("6"; "Usage")
                {
                    ApplicationArea = All;
                }
                field(Selection; SelectionText)
                {
                    ApplicationArea = All;
                    Caption = 'Selection';
                }
            }
        }
        area(FactBoxes)
        {
            part("Setup"; "Sample Temp.Setup FactB")
            {
                ApplicationArea = All;
                SubPageLink = "Template Code" = FIELD("TemplateCode");
            }
            part("Template Lines"; "Sample Template Line FactBox")
            {
                ApplicationArea = All;
                SubPageLink = "Template Code" = FIELD("TemplateCode");
            }
        }
    }
    actions
    {
        area(Processing)
        {
            action(MergeFields)
            {
                ApplicationArea = All;
                Caption = 'Merge Fields';
                Image = "SelectField";
                Promoted = true;
                PromotedCategory = Category4;
                PromotedIsBig = true;
                PromotedOnly = true;
                Scope = Repeater;
                RunObject = page "Sample Template MergeFields";
                RunPageLink = "Template Code" = field("TemplateCode");
            }
            action(MergeTables)
            {
                ApplicationArea = All;
                Caption = 'Merge Tables';
                Image = "Table";
                Promoted = true;
                PromotedCategory = Category4;
                PromotedIsBig = true;
                PromotedOnly = true;
                Scope = Repeater;
                RunObject = page "Sample Template MergeTables";
                RunPageLink = "Template Code" = field("TemplateCode");
            }
            action(ShowSetup)
            {
                ApplicationArea = All;
                Caption = 'Setup';
                Image = "MailSetup";
                Promoted = true;
                PromotedCategory = Category4;
                PromotedIsBig = true;
                PromotedOnly = true;
                Scope = Repeater;
                trigger OnAction()
                var
                    Management: Codeunit "Sample Management";
                begin
                    Management.ShowSetup(Rec);
                end;
            }
            action(Log)
            {
                ApplicationArea = All;
                Caption = 'Log';
                Image = "Journals";
                Promoted = true;
                PromotedCategory = Category4;
                PromotedOnly = true;
                RunObject = page "Sample Log";
                RunPageLink = "Template Code" = field("TemplateCode");
                RunPageView = sorting("Template Code", "Language Code");
            }
            action(CopyTemplate)
            {
                ApplicationArea = All;
                Caption = 'Copy Template';
                Image = "Copy";
                Promoted = true;
                PromotedCategory = Category4;
                PromotedOnly = true;
                RunObject = report "Sample Copy Template";
            }
            action(OnlineHub)
            {
                ApplicationArea = All;
                Caption = 'Online Hub';
                Image = UserInterface;
                ToolTip = 'Access relevant resources, guides, and documentation.';
                Promoted = true;
                PromotedCategory = Category4;
                PromotedOnly = true;

                trigger OnAction()
                var
                    Hub: Codeunit "Sample Hub";
                begin
                    Hub.OpenHub(Page::"Sample E-Mail Template Card");
                end;
            }
            action(Download)
            {
                ApplicationArea = All;
                Caption = 'Download';
                Image = "ElectronicDoc";
                Promoted = true;
                PromotedCategory = Category5;
                PromotedOnly = true;
                ToolTip = 'Downloads default templates online.';
                trigger OnAction()
                var
                    DownloadPage: Page "Sample Download Page";
                begin
                    DownloadPage.LookupMode := true;
                    if DownloadPage.RunModal = Action::LookupOK then
                        DownloadPage.DownloadAndImport();
                end;
            }
            action(Import)
            {
                ApplicationArea = All;
                Caption = 'Import';
                Image = "Import";
                Promoted = true;
                PromotedCategory = Category6;
                PromotedOnly = true;
                ToolTip = 'Imports templates from an XML file.';
                trigger OnAction()
                var
                    ImportExport: Codeunit "Sample ImportExport";
                begin
                    ImportExport.ImportXMLDialog;
                end;
            }
            action(Export)
            {
                ApplicationArea = All;
                Caption = 'Export';
                Image = "Export";
                Promoted = true;
                PromotedCategory = Category6;
                PromotedOnly = true;
                ToolTip = 'Exports templates to an XML file.';
                trigger OnAction()
                var
                    TemplateHeader: Record "Sample E-Mail Template Header";
                    ImportExport: Codeunit "Sample ImportExport";
                begin
                    CurrPage.SetSelectionFilter(TemplateHeader);
                    ImportExport.ExportAsXMLDialog(TemplateHeader);
                end;
            }
        }
    }
    trigger OnOpenPage()
    begin
        Codeunit.Run(Codeunit::"Sample Convert");
    end;

    trigger OnAfterGetRecord()
    begin
        SelectionText := GetSelection;
    end;

    var
        SelectionText: Text;
}
